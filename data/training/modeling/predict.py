"""Production daily prediction job: builds tomorrow's calendar grid for
every kept zone, fetches tomorrow's live weather forecast (via
weather/forecast.py, the same coordinate used for training), predicts
deviation with the trained model, adds back the historical norm to get an
absolute busyness prediction, and derives the human-readable "level" label.

Deliberately out of scope here: mapping
zone IDs to the application's internal area identifiers and writing to the
application's database - those are app-integration concerns, not Data/ML
ones, and this rebuild has no legitimate database target or credentials for
them. This module's responsibility ends at producing a correctly-labelled
prediction table; by default it does not persist anything, and only writes
to config.PREDICTIONS_PATH when explicitly asked (dry_run=False).

Predictions are NOT clipped to [0, 1] - a deliberate, disclosed choice: 
values that fall slightly outside the valid range are kept as legitimate
extrapolations rather than artificially clamped.

The "level" label uses the hybrid rule: the absolute score decides the
label outright at the extremes (below the floor is always "not busy",
above the ceiling is always "busier"); only in the ambiguous middle band
does the predicted deviation-from-norm decide between the three labels.
"""

import json

import lightgbm as lgb
import pandas as pd

import config
from features.build_features import WEATHER_RENAME, add_calendar_features
from geo import zones
from modeling.train import prepare_model_input
from weather import forecast


def build_tomorrow_grid() -> pd.DataFrame:
    kept_zone_ids = sorted(zones.get_kept_zone_ids())
    start, _ = forecast.get_tomorrow_local_range()
    hours = pd.date_range(start, periods=24, freq="h")
    grid = pd.MultiIndex.from_product(
        [kept_zone_ids, hours], names=[config.COL_ZONE, config.COL_HOUR]
    ).to_frame(index=False)
    return add_calendar_features(grid)


def load_artifacts():
    booster = lgb.Booster(model_file=str(config.MODEL_PATH))
    norm_table = pd.read_csv(config.NORM_TABLE_PATH)
    with open(config.FEATURE_COLS_PATH) as f:
        feature_cols = json.load(f)
    with open(config.LEVEL_THRESHOLDS_PATH) as f:
        level_thresholds = json.load(f)
    return booster, norm_table, feature_cols, level_thresholds


def compute_level(busyness_score: pd.Series, deviation, thresholds: dict) -> pd.Series:
    floor = thresholds["floor"]
    ceiling = thresholds["ceiling"]
    deadband = thresholds["deadband"]
    not_busy, as_usual, busier = thresholds["labels"]
    deviation = pd.Series(deviation, index=busyness_score.index)

    level = pd.Series(as_usual, index=busyness_score.index)
    middle = (busyness_score > floor) & (busyness_score < ceiling)
    level.loc[middle & (deviation > deadband)] = busier
    level.loc[middle & (deviation < -deadband)] = not_busy
    level.loc[busyness_score <= floor] = not_busy
    level.loc[busyness_score >= ceiling] = busier
    return level


def predict(dry_run: bool = True) -> pd.DataFrame:
    booster, norm_table, feature_cols, level_thresholds = load_artifacts()

    grid = build_tomorrow_grid()
    weather_df = forecast.fetch_tomorrow().rename(columns=WEATHER_RENAME)
    grid = grid.merge(weather_df, on=config.COL_HOUR, how="left")
    grid = grid.merge(
        norm_table.rename(columns={"norm_value": "norm"}),
        on=[config.COL_ZONE, "day_of_week", "hour"],
        how="left",
    )

    X = prepare_model_input(grid, feature_cols=feature_cols)
    # No num_iteration argument: the saved model file already contains only
    # the trees up to its best_iteration (see modeling/train.py), since
    # best_iteration itself does not survive a save/load round trip.
    predicted_deviation = booster.predict(X)
    grid["busyness_score"] = grid["norm"] + predicted_deviation
    grid["level"] = compute_level(grid["busyness_score"], predicted_deviation, level_thresholds)

    result = grid[[config.COL_ZONE, config.COL_HOUR, "busyness_score", "level"]]

    if not dry_run:
        config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        result.to_csv(config.PREDICTIONS_PATH, index=False)

    return result
