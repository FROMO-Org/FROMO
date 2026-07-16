"""
data/predictions.py — Daily busyness prediction pipeline
==========================================================
Fetches tomorrow's weather (Open-Meteo), builds calendar features,
predicts deviation from norm via the committed LightGBM model, and upserts
predicted busyness scores into Supabase.

Usage:
    python predictions.py               # full run, writes to Supabase
    python predictions.py --dry-run     # full pipeline (real weather fetch +
                                         # real prediction), skips the Supabase
                                         # write and just logs a preview.
                                         # No Supabase credentials required.
"""

import argparse
import datetime
import json
import logging
import os
import sys
from datetime import timedelta, timezone as dt_timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import holidays
import lightgbm as lgb
import openmeteo_requests
import pandas as pd
import requests_cache
from dotenv import load_dotenv
from retry_requests import retry

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("predictions")

# ── Artifacts ──────────────────────────────────────────────────────────────
MODEL_PATH = BASE_DIR / "model.txt"
NORM_PATH = BASE_DIR / "norm_table.csv"
FEATURE_COLS_PATH = BASE_DIR / "feature_cols.json"
CACHE_PATH = str(BASE_DIR / ".cache")

# ── Weather ────────────────────────────────────────────────────────────────
LATITUDE = 40.7831
LONGITUDE = -73.9712
HOURLY_VARS = ["temperature_2m", "apparent_temperature", "precipitation", "snowfall"]
WEATHER_COLS = ["temperature", "apparent_temperature", "precipitation", "snowfall"]

# ── Supabase ───────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SOURCE_TAG = "daily_lightgbm_pipeline"

# ── Level thresholds ─────────────────────────────────────────────────────
# Hybrid scheme: absolute predicted_busyness overrides at the extremes;
# predicted_deviation (this zone's own norm) decides the label in the
# ambiguous middle band. FLOOR/CEILING are the historical (all-time) 33rd/
# 66th percentile of busyness_score across the full training set — not
# 0.33/0.66, which sit above the 95th percentile of actual scores.
LEVEL_FLOOR = 0.07
LEVEL_CEILING = 0.22
LEVEL_DEADBAND = 0.02


def get_ny_tomorrow() -> datetime.date:
    """Single source of truth for 'tomorrow' — NY-local calendar date."""
    return datetime.datetime.now(ZoneInfo("America/New_York")).date() + datetime.timedelta(days=1)


def generate_tomorrow_calendar(location_ids, tomorrow: datetime.date) -> pd.DataFrame:
    """Generates a 24-hour baseline dataframe for `tomorrow` for every location id."""
    day_of_week = pd.Timestamp(tomorrow).dayofweek  # Monday=0 … Sunday=6
    day_of_year = pd.Timestamp(tomorrow).dayofyear
    month = tomorrow.month
    day_of_month = tomorrow.day

    ny_holidays = holidays.country_holidays("US", subdiv="NY", years=[tomorrow.year])
    is_holiday = tomorrow in ny_holidays

    records = []
    for loc_id in location_ids:
        for hour in range(24):
            records.append(
                {
                    "date": pd.Timestamp(tomorrow),
                    "locationid": loc_id,
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "day_of_year": day_of_year,
                    "month": month,
                    "day_of_month": day_of_month,
                    "is_holiday": is_holiday,
                }
            )
    return pd.DataFrame(records)


def fetch_weather(ny_tomorrow: datetime.date) -> pd.DataFrame:
    """Fetches tomorrow's hourly weather forecast (NY-local hours) from Open-Meteo."""
    cache_session = requests_cache.CachedSession(CACHE_PATH, expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": HOURLY_VARS,
        "timezone": "America/New_York",
        "start_date": (ny_tomorrow - datetime.timedelta(days=1)).isoformat(),
        "end_date": (ny_tomorrow + datetime.timedelta(days=1)).isoformat(),
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    tz = dt_timezone(timedelta(seconds=response.UtcOffsetSeconds()))

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(tz),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(tz),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    for i, var_name in enumerate(HOURLY_VARS):
        hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    mask = hourly_dataframe["date"].dt.date == ny_tomorrow
    hourly_dataframe = hourly_dataframe[mask].reset_index(drop=True)

    hourly_dataframe["hour"] = hourly_dataframe["date"].dt.hour
    hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"].dt.date)
    hourly_dataframe = hourly_dataframe.rename(columns={"temperature_2m": "temperature"})

    return hourly_dataframe[["date", "hour"] + WEATHER_COLS]


def predict(pipeline_df: pd.DataFrame) -> pd.DataFrame:
    """Loads the LightGBM booster and adds a predicted_deviation column."""
    with open(FEATURE_COLS_PATH) as f:
        feature_cols = json.load(f)

    booster = lgb.Booster(model_file=str(MODEL_PATH))

    missing_cols = [c for c in feature_cols if c not in pipeline_df.columns]
    if missing_cols:
        raise ValueError(f"pipeline_df is missing required feature columns: {missing_cols}")

    X = pipeline_df[feature_cols].copy()
    # locationid must be category dtype — the booster carries its own
    # pandas_categorical mapping and remaps codes internally.
    X["locationid"] = X["locationid"].astype("category")

    pipeline_df["predicted_deviation"] = booster.predict(X)
    logger.info("Predicted %d rows", len(pipeline_df))
    return pipeline_df


def apply_norm(pipeline_df: pd.DataFrame, norm_table: pd.DataFrame) -> pd.DataFrame:
    """predicted_busyness = norm + predicted_deviation"""
    pipeline_df = pipeline_df.merge(
        norm_table.rename(columns={"norm_value": "norm"}),
        on=["locationid", "day_of_week", "hour"],
        how="left",
    )

    n_missing_norm = pipeline_df["norm"].isnull().sum()
    if n_missing_norm > 0:
        raise ValueError(
            f"{n_missing_norm} rows have no matching norm — check location ids vs norm_table zones"
        )

    pipeline_df["predicted_busyness"] = pipeline_df["norm"] + pipeline_df["predicted_deviation"]

    logger.info(
        "predicted_busyness range: [%.4f, %.4f]",
        pipeline_df["predicted_busyness"].min(), pipeline_df["predicted_busyness"].max(),
    )
    out_of_range = (
        (pipeline_df["predicted_busyness"] < 0) | (pipeline_df["predicted_busyness"] > 1)
    ).sum()
    if out_of_range > 0:
        logger.warning(
            "%d predicted_busyness value(s) outside [0,1] — extrapolations, retained as-is",
            out_of_range,
        )
    return pipeline_df


def compute_level(pipeline_df: pd.DataFrame) -> pd.DataFrame:
    """Adds `level`: 'not busy' | 'as usual' | 'busier'.

    score >= LEVEL_CEILING           -> "busier"   (absolute override)
    score <= LEVEL_FLOOR             -> "not busy" (absolute override)
    otherwise, deviation >= LEVEL_DEADBAND  -> "busier"
               deviation <= -LEVEL_DEADBAND -> "not busy"
               else                          -> "as usual"
    """
    def _level(row):
        score = row["predicted_busyness"]
        dev = row["predicted_deviation"]
        if score >= LEVEL_CEILING:
            return "busier"
        if score <= LEVEL_FLOOR:
            return "not busy"
        if dev >= LEVEL_DEADBAND:
            return "busier"
        if dev <= -LEVEL_DEADBAND:
            return "not busy"
        return "as usual"

    pipeline_df["level"] = pipeline_df.apply(_level, axis=1)
    logger.info("level distribution:\n%s", pipeline_df["level"].value_counts().to_string())
    return pipeline_df


def map_area_ids(pipeline_df: pd.DataFrame, supabase) -> pd.DataFrame:
    """busyness_areas.id (uuid) <-> busyness_areas.locationid (int)"""
    areas_response = supabase.table("busyness_areas").select("id, locationid").execute()
    area_mapping = pd.DataFrame(areas_response.data).rename(columns={"id": "area_id"})

    pipeline_df = pipeline_df.merge(area_mapping, on="locationid", how="left")

    n_missing_area = pipeline_df["area_id"].isnull().sum()
    if n_missing_area > 0:
        missing_zones = sorted(
            pipeline_df.loc[pipeline_df["area_id"].isnull(), "locationid"].unique()
        )
        raise ValueError(
            f"{n_missing_area} rows have no matching area_id — locationids missing "
            f"from busyness_areas: {missing_zones}"
        )

    logger.info("Mapped %d zones to area_id", pipeline_df["area_id"].nunique())
    return pipeline_df


def push_predictions(pipeline_df: pd.DataFrame, supabase) -> None:
    """Insert new predictions for this day-of-week. Insert-only — no delete.

    Old prediction rows for this pipeline's prior forecasts are left in
    place rather than replaced. The app always reads the row with the
    latest observed_at per area, so old rows just become inert once a
    fresher one is inserted — there's no need to clean them up for
    correctness. This intentionally avoids doing a delete + insert as two
    separate, non-transactional Supabase calls: if the run failed between
    them, a day-of-week could be left with zero prediction rows until the
    next weekly cycle. Insert-only has no such gap — a failed insert simply
    leaves the previous rows in place.
    """
    # observed_at is a log/audit field only (local_day_of_week/local_hour are
    # what the app actually reads) — store it as naive UTC to match the
    # utc_now_naive()/to_naive_utc() convention used everywhere else in the
    # app for `timestamp without time zone` columns, rather than leaving it
    # in NY-local wall-clock time.
    ny_dt = pipeline_df["date"] + pd.to_timedelta(pipeline_df["hour"], unit="h")
    observed_at_utc = (
        ny_dt.dt.tz_localize(
            ZoneInfo("America/New_York"), ambiguous="NaT", nonexistent="shift_forward"
        )
        .dt.tz_convert(dt_timezone.utc)
        .dt.tz_localize(None)
    )

    records = pipeline_df.assign(
        observed_at=observed_at_utc.dt.strftime("%Y-%m-%dT%H:%M:%S"),
        local_day_of_week=pipeline_df["day_of_week"],
        local_hour=pipeline_df["hour"],
        score=pipeline_df["predicted_busyness"].round(2),
        is_prediction=True,
        source=SOURCE_TAG,
    )[["area_id", "observed_at", "local_day_of_week", "local_hour", "score", "level", "is_prediction", "source"]]

    payload = records.to_dict(orient="records")
    # Coerce numpy scalar types (int64/float32/bool_) to native Python types —
    # the Supabase client's JSON encoder rejects numpy types.
    payload = [
        {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
        for row in payload
    ]

    insert_resp = supabase.table("busyness_scores").insert(payload).execute()
    logger.info("Inserted %d new prediction rows", len(insert_resp.data))


def parse_args():
    parser = argparse.ArgumentParser(description="Daily busyness prediction pipeline")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run the full pipeline (real weather fetch + real prediction) but skip the "
             "Supabase write. No Supabase credentials required.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ny_tomorrow = get_ny_tomorrow()
    logger.info("Predicting for NY date: %s", ny_tomorrow)

    norm_table = pd.read_csv(NORM_PATH)
    location_ids = sorted(norm_table["locationid"].unique().tolist())

    tomorrow_df = generate_tomorrow_calendar(location_ids, ny_tomorrow)
    logger.info(
        "tomorrow_df shape: %s (expect %d zones x 24 hours = %d)",
        tomorrow_df.shape, len(location_ids), len(location_ids) * 24,
    )

    weather_df = fetch_weather(ny_tomorrow)
    pipeline_df = tomorrow_df.merge(weather_df, on=["date", "hour"], how="left")

    n_missing_weather = pipeline_df[WEATHER_COLS].isnull().any(axis=1).sum()
    if n_missing_weather > 0:
        raise ValueError(
            f"{n_missing_weather} rows have no matching weather data after merge — "
            f"check for a date/timezone mismatch between tomorrow_df and the Open-Meteo response"
        )

    pipeline_df = predict(pipeline_df)
    pipeline_df = apply_norm(pipeline_df, norm_table)
    pipeline_df = compute_level(pipeline_df)

    if args.dry_run:
        logger.info("Dry run — skipping Supabase write")
        preview = pipeline_df[
            ["locationid", "date", "hour", "norm", "predicted_deviation", "predicted_busyness", "level"]
        ].head(10)
        logger.info("Preview:\n%s", preview.to_string())
        return

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set as environment variables "
            "(e.g. in data/.env locally, or as GitHub Actions secrets)."
        )

    from supabase import create_client

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    pipeline_df = map_area_ids(pipeline_df, supabase)
    push_predictions(pipeline_df, supabase)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Daily prediction run failed")
        sys.exit(1)
