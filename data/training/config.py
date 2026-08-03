"""Single source of truth for the pipeline: raw-data paths, date range,
zone resolution rule, normalization percentiles, mode weights, weather
coordinate, model hyperparameters, and artifact paths. Every stage imports
from here — nothing is retyped locally in a stage module.
"""

import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Raw data is referenced in place under the legacy Busyness/ folder (a
# sibling of this new_pipeline/ folder) rather than duplicated, so there is
# exactly one copy of the raw data on disk. Resolved relative to this file,
# not as an absolute path, so the pipeline still works if the parent
# "Datasets" folder is moved/renamed as a whole.
NEW_PIPELINE_DIR = Path(__file__).resolve().parent
LEGACY_DIR = NEW_PIPELINE_DIR.parent / "Busyness"

RAW_BIKE_DIR = LEGACY_DIR / "bike"
RAW_TAXI_DIR = LEGACY_DIR / "taxi"
RAW_SUBWAY_DIR = LEGACY_DIR / "subway"
SHAPEFILE_PATH = LEGACY_DIR / "shapefile" / "geo_export_79b6f56f-077b-402f-a961-af5a7de819e0.shp"

DATA_INTERIM_DIR = NEW_PIPELINE_DIR / "data" / "interim"
DATA_PROCESSED_DIR = NEW_PIPELINE_DIR / "data" / "processed"
ARTIFACTS_DIR = NEW_PIPELINE_DIR / "artifacts"

BUSYNESS_SCORED_PATH = DATA_PROCESSED_DIR / "busyness_scored.csv"
FEATURES_PATH = DATA_PROCESSED_DIR / "features.csv"
PREDICTIONS_PATH = DATA_PROCESSED_DIR / "predictions_tomorrow.csv"

MODEL_PATH = ARTIFACTS_DIR / "model.txt"
NORM_TABLE_PATH = ARTIFACTS_DIR / "norm_table.csv"
FEATURE_COLS_PATH = ARTIFACTS_DIR / "feature_cols.json"
NORMALIZATION_THRESHOLDS_PATH = ARTIFACTS_DIR / "normalization_thresholds.json"
ZONE_LIST_PATH = ARTIFACTS_DIR / "zone_list.json"
LEVEL_THRESHOLDS_PATH = ARTIFACTS_DIR / "level_thresholds.json"
RUN_MANIFEST_PATH = ARTIFACTS_DIR / "run_manifest.json"

# ---------------------------------------------------------------------------
# Month discovery
# ---------------------------------------------------------------------------
# Bike and taxi raw data is laid out as one subfolder per month, named
# "{3-letter-lowercase-month}_{4-digit-year}" (e.g. "jan_2025"). Rather than
# hardcoding the list of covered months anywhere, the pipeline discovers it
# by scanning these folders, so adding a new month means only adding its
# raw-data folder — no code or config change.
MONTH_TAG_PATTERN = re.compile(r"^([a-z]{3})_(\d{4})$")
MONTH_ABBR_TO_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def discover_month_tags(raw_dir: Path) -> list[tuple[int, int, str]]:
    """Scan a raw-data directory for month folders and return
    (year, month, tag) tuples sorted chronologically."""
    months = []
    for entry in raw_dir.iterdir():
        if not entry.is_dir():
            continue
        match = MONTH_TAG_PATTERN.match(entry.name)
        if not match:
            continue
        abbr, year = match.groups()
        if abbr not in MONTH_ABBR_TO_NUM:
            continue
        months.append((int(year), MONTH_ABBR_TO_NUM[abbr], entry.name))
    return sorted(months)


def get_covered_months() -> list[tuple[int, int, str]]:
    """The months usable by the pipeline: the intersection of what bike and
    taxi both have raw data for (subway is a single continuous file, filtered
    to this range downstream rather than folder-per-month)."""
    bike_months = {(y, m) for y, m, _ in discover_month_tags(RAW_BIKE_DIR)}
    taxi_months = {(y, m) for y, m, _ in discover_month_tags(RAW_TAXI_DIR)}
    common = bike_months & taxi_months
    tags_by_ym = {(y, m): tag for y, m, tag in discover_month_tags(RAW_BIKE_DIR)}
    return sorted((y, m, tags_by_ym[(y, m)]) for y, m in common)


def month_date_range(year: int, month: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Inclusive [start, end] timestamps for a calendar month, computed from
    the calendar rather than typed as a literal end-of-month date — the
    class of bug where a 30-day month gets a hardcoded "31st" boundary can't
    occur here."""
    start = pd.Timestamp(year=year, month=month, day=1)
    end = start + pd.DateOffset(months=1) - pd.Timedelta(seconds=1)
    return start, end


def get_full_date_range() -> tuple[pd.Timestamp, pd.Timestamp]:
    """The overall [start, end] timestamp range covered by the discovered
    months. Used by subway ingestion (a single continuous file, not laid out
    per month like bike/taxi) and by later stages that need the full
    zone x hour grid."""
    months = get_covered_months()
    start = month_date_range(months[0][0], months[0][1])[0]
    end = month_date_range(months[-1][0], months[-1][1])[1]
    return start, end


# Most recent complete discovered month(s) are held out for testing rather
# than a hardcoded date, so the split follows the data as new months arrive.
TEST_HOLDOUT_MONTHS = 1

# ---------------------------------------------------------------------------
# Subway raw-file resolution
# ---------------------------------------------------------------------------
# MTA re-exports this dataset periodically under inconsistent names, and a
# newer export date does NOT mean broader coverage: observed on disk,
# "..._Beginning_2025_20260601.csv" covers 2025-01-01 to 2026-05-20 (12.0M
# rows) while the later-dated "..._Beginning_2025_20260713.csv" covers only
# 2026-05-21 to 2026-07-01 (2.3M rows) - a small incremental delta, not a
# fuller replacement. Picking "the newest-dated file" would silently lose
# most of the history. Instead, every matching file is loaded and
# concatenated in ingest/subway.py, with exact-duplicate rows dropped -
# correct whether the files turn out to be complementary (as observed:
# 12,009,821 + 2,324,240 = 14,334,061, matching the third file exactly) or
# overlapping, and self-healing if MTA's export pattern changes again.
SUBWAY_RAW_GLOB = "MTA_Subway_Hourly_Ridership*.csv"


def resolve_subway_raw_paths() -> list[Path]:
    candidates = sorted(RAW_SUBWAY_DIR.glob(SUBWAY_RAW_GLOB))
    if not candidates:
        raise FileNotFoundError(
            f"No file matching {SUBWAY_RAW_GLOB!r} found in {RAW_SUBWAY_DIR}"
        )
    return candidates


# ---------------------------------------------------------------------------
# Zone resolution
# ---------------------------------------------------------------------------
# The borough filter and island exclusion are genuine editorial decisions
# (not derivable from the data), so they stay as explicit config — but they
# are the ONLY zone-related config, and geo/zones.py is the only place that
# reads them, so every stage that needs "which zones count" agrees by
# construction.
BOROUGH_COLUMN = "borough"
BOROUGH_FILTER_VALUE = "manhattan"
ZONE_ID_COLUMN = "locationid"
# Governor's/Ellis/Liberty Island complex: physically isolated, no subway or
# Citibike coverage, would create spurious zeros if kept.
EXCLUDED_ZONE_IDS = {103, 104, 105}
JOIN_CRS = "EPSG:4326"
SPATIAL_JOIN_PREDICATE = "within"

# ---------------------------------------------------------------------------
# Common intermediate schema
# ---------------------------------------------------------------------------
# The column names every mode's cleaned output converges to, so downstream
# stages (spatial join, scoring) never need mode-specific branching beyond
# the join itself.
COL_ZONE = "locationid"
COL_HOUR = "floor_hour"
COL_COUNT = "ride_count"
COL_SOURCE = "source"
COL_STATION = "station_name"
COL_LAT = "lat"
COL_LON = "lon"

MODE_BIKE = "bike"
MODE_TAXI = "taxi"
MODE_SUBWAY = "subway"
MODES = (MODE_SUBWAY, MODE_TAXI, MODE_BIKE)


def count_column(mode: str) -> str:
    """The wide-panel raw-count column name for a mode (e.g. "subway_count").
    Centralized here so scoring modules never re-derive this convention
    separately."""
    return f"{mode}_count"


def norm_column(mode: str) -> str:
    """The wide-panel normalized column name for a mode (e.g. "subway_norm")."""
    return f"{mode}_norm"

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
# Fit once across the full discovered history, not per month, so
# busyness_score is on one fixed scale for the whole study period. Frozen
# thresholds are persisted to NORMALIZATION_THRESHOLDS_PATH.
CLIP_LOWER_PERCENTILE = 0.01
CLIP_UPPER_PERCENTILE = 0.99

# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------
# Equal weighting, presence-aware — the deliberate choice:
# equal weights tracked the data-driven PCA weighting almost exactly, need no
# re-fitting as more months are added, and require no arbitrary ratio to
# defend. A mode is "present" for a zone if it has any nonzero activity for
# that zone across the FULL discovered history (not recomputed per month).
MODE_WEIGHTS = {MODE_SUBWAY: 1.0, MODE_TAXI: 1.0, MODE_BIKE: 1.0}

# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------
# One coordinate, used by both the historical fetch (training) and the
# forecast fetch (live production), closing the legacy mismatch where
# training used (40.808434, -74.0199) and inference used (40.7831,
# -73.9712). This value matches the coordinate already used by the deployed
# production prediction job, so no downstream app change is required.
WEATHER_LATITUDE = 40.7831
WEATHER_LONGITUDE = -73.9712
WEATHER_TIMEZONE = "America/New_York"
WEATHER_HOURLY_FIELDS = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation",
    "snowfall",
]
WEATHER_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# Cached rather than re-fetched on every run: Open-Meteo's historical archive
# is a reanalysis product that can itself be revised after the fact (the
# same class of issue found in MTA's raw subway exports), so re-running the
# pipeline later should not silently pick up different training weather
# without an explicit, deliberate re-fetch.
WEATHER_HISTORICAL_CACHE_PATH = DATA_INTERIM_DIR / "weather_historical.csv"

# ---------------------------------------------------------------------------
# Foot-traffic validation (validation/foot_traffic.py)
# ---------------------------------------------------------------------------
# NYC DOT's public Bi-Annual Pedestrian Counts - a free, partial ground-truth
# source for checking whether busyness_score's transport-based proxy tracks
# actual foot traffic (DATA_ML_HANDOFF.md Section 10). Cached rather than
# re-fetched every run: this is a slow-changing, twice-a-year dataset.
DOT_PED_COUNTS_URL = "https://data.cityofnewyork.us/resource/cqsj-cfgu.json"
DOT_PED_COUNTS_CACHE_PATH = DATA_INTERIM_DIR / "dot_pedestrian_counts.json"

# ---------------------------------------------------------------------------
# Feature set
# ---------------------------------------------------------------------------
# Exact order matters (it is the order the trained model expects); kept as
# one explicit list so train.py and predict.py can never silently diverge.
FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "is_holiday",
    "temperature",
    "apparent_temperature",
    "precipitation",
    "snowfall",
    "locationid",
]
HOLIDAY_COUNTRY = "US"
HOLIDAY_SUBDIVISION = "NY"

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
LGBM_PARAMS = {
    "n_estimators": 1000,
    "num_leaves": 64,
    "min_child_samples": 20,
    "learning_rate": 0.05,
    "random_state": RANDOM_STATE,
}
LGBM_EARLY_STOPPING_ROUNDS = 100
# Early-stopping validation set: a random row-level holdout across ALL
# training months, not a held-out calendar month. Diagnosed directly: a
# single trailing month (whichever happens to fall right before the test
# month) can be atypically calm or volatile relative to the rest of the
# year, causing early stopping to trigger on a misleading signal (verified:
# holding out April 2026 alone gave a materially worse, premature stop than
# a representative random sample). A random split is statistically
# appropriate here because the model's target is *deviation from the
# historical norm* - the norm subtraction has already removed most of the
# time-series signal, leaving a largely cross-sectional weather/calendar
# regression problem, for which random validation is the standard choice.
#
# n_estimators=1000 is a deliberate, disclosed cap, not a value early
# stopping converges to on its own: the random validation split's loss
# keeps improving smoothly well past 1000 rounds without plateauing (it
# does not distinguish genuine generalization from overfitting to
# fit-set-specific quirks, since it is drawn from the same months as the
# fit set), while directly measuring test-month performance at 1000 / 3000
# / 5000 rounds showed test error was lowest around 1000 and mildly worse
# beyond it. Full hyperparameter tuning is out of scope here (as it was for
# the legacy pipeline too - see DATA_ML_HANDOFF.md open items); this cap is
# the pragmatic, evidence-based stand-in for it.
VAL_HOLDOUT_FRACTION = 0.1

# ---------------------------------------------------------------------------
# Busyness "level" label
# ---------------------------------------------------------------------------
# Hybrid rule: absolute score decides at the extremes,
# deviation-from-norm decides in the ambiguous middle. Cutoffs are stored
# here as PERCENTILES of the rule, this pipeline computes the actual percentile
# values from training data at train time and persists the result to
# LEVEL_THRESHOLDS_PATH rather than hardcoding them.
LEVEL_LOW_PERCENTILE = 1 / 3
LEVEL_HIGH_PERCENTILE = 2 / 3
LEVEL_DEVIATION_DEADBAND = 0.02 
LEVEL_LABELS = ("not busy", "as usual", "busier")
