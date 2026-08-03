"""Expanding-window historical-norm computation, deviation target, and
LightGBM training. The model predicts the deviation of busyness_score from
its own historically-expected (zone, day_of_week, hour) norm, not the level
directly - this isolates the learnable weather/calendar signal from the
already-known periodic pattern (validated in the legacy pipeline against a
direct-level model). Exports the model, norm lookup table, feature list,
and level-label thresholds to artifacts/.

Leakage prevention: for every non-first training month, the norm is
computed only from strictly prior months (expanding window). The first
training month has no prior history at all; it is filled from the static
full-training profile instead - a deliberate, bounded exception affecting
only that one month, inherited from the legacy pipeline's disclosed
approach. The held-out test month's norm uses the same static
full-training profile, which is leakage-safe since the test month is
chronologically after every training month.

Validation split for early stopping: a random row-level holdout across all
training months (config.VAL_HOLDOUT_FRACTION), not a held-out calendar
month. Diagnosed directly while building this module: holding out the
single most recent training month gave a misleading early-stopping signal
whenever that particular month happened to be atypically calm or volatile
relative to the rest of the year (verified concretely - see config.py's
LGBM_PARAMS comment). A random split is statistically appropriate because
the model's target is deviation *from* the historical norm - the norm
subtraction has already removed most of the time-series signal, leaving a
largely cross-sectional weather/calendar regression problem. The outer
test split remains strictly chronological (the most recent
TEST_HOLDOUT_MONTHS months), which is the split that actually matters for
leakage prevention.
"""

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

import config
from geo import zones


def _ym(series: pd.Series) -> pd.Series:
    return series.dt.year * 100 + series.dt.month


def _month_ym(year: int, month: int) -> int:
    return year * 100 + month


def split_months(months=None):
    """(trainval_yms, test_yms): test is the most recent
    TEST_HOLDOUT_MONTHS discovered months; trainval is everything before
    that (further split into fit/val by split_fit_val, at the row level)."""
    months = months if months is not None else config.get_covered_months()
    yms = [_month_ym(y, m) for y, m, _ in months]
    n = config.TEST_HOLDOUT_MONTHS
    test_yms = yms[-n:]
    trainval_yms = yms[:-n]
    return trainval_yms, test_yms


def split_fit_val(trainval_df: pd.DataFrame):
    """Random row-level holdout for early-stopping - see module docstring
    for why this is a random split rather than a held-out month."""
    rng = np.random.default_rng(config.RANDOM_STATE)
    is_val = rng.random(len(trainval_df)) < config.VAL_HOLDOUT_FRACTION
    return trainval_df.loc[~is_val], trainval_df.loc[is_val]


def compute_norm_profile(df: pd.DataFrame):
    """(zone, day_of_week, hour) mean busyness_score, plus coarser (zone,
    hour) and zone-overall fallbacks for bins with insufficient history."""
    fine = (
        df.groupby([config.COL_ZONE, "day_of_week", "hour"])["busyness_score"]
        .mean()
        .rename("norm_fine")
        .reset_index()
    )
    coarse = (
        df.groupby([config.COL_ZONE, "hour"])["busyness_score"]
        .mean()
        .rename("norm_coarse")
        .reset_index()
    )
    zone_overall = (
        df.groupby(config.COL_ZONE)["busyness_score"]
        .mean()
        .rename("norm_zone")
        .reset_index()
    )
    return fine, coarse, zone_overall


def apply_norm_profile(df: pd.DataFrame, fine, coarse, zone_overall) -> pd.Series:
    merged = df.merge(fine, on=[config.COL_ZONE, "day_of_week", "hour"], how="left")
    merged = merged.merge(coarse, on=[config.COL_ZONE, "hour"], how="left")
    merged = merged.merge(zone_overall, on=config.COL_ZONE, how="left")
    return merged["norm_fine"].fillna(merged["norm_coarse"]).fillna(merged["norm_zone"])


def compute_expanding_norms(trainval_df: pd.DataFrame) -> pd.Series:
    yms = sorted(trainval_df["_ym"].unique())
    first_ym = yms[0]

    static_profile = compute_norm_profile(trainval_df)
    norm = pd.Series(index=trainval_df.index, dtype=float)

    first_mask = (trainval_df["_ym"] == first_ym).to_numpy()
    norm.loc[first_mask] = apply_norm_profile(
        trainval_df.loc[first_mask], *static_profile
    ).to_numpy()

    for ym in yms[1:]:
        history = trainval_df.loc[trainval_df["_ym"] < ym]
        profile = compute_norm_profile(history)
        rows_mask = (trainval_df["_ym"] == ym).to_numpy()
        norm.loc[rows_mask] = apply_norm_profile(
            trainval_df.loc[rows_mask], *profile
        ).to_numpy()

    return norm


def build_norm_table(trainval_df: pd.DataFrame) -> pd.DataFrame:
    """The final (zone, day_of_week, hour) -> norm_value lookup: used to
    fill the test set's norm and exported for production. Complete for
    every zone x day_of_week x hour combination (66 x 7 x 24 = 11,088 rows)
    via the same fine -> coarse -> zone-overall fallback chain."""
    fine, coarse, zone_overall = compute_norm_profile(trainval_df)
    kept_zone_ids = sorted(zones.get_kept_zone_ids())
    skeleton = pd.MultiIndex.from_product(
        [kept_zone_ids, range(7), range(24)],
        names=[config.COL_ZONE, "day_of_week", "hour"],
    ).to_frame(index=False)

    table = skeleton.merge(fine, on=[config.COL_ZONE, "day_of_week", "hour"], how="left")
    table = table.merge(coarse, on=[config.COL_ZONE, "hour"], how="left")
    table = table.merge(zone_overall, on=config.COL_ZONE, how="left")
    table["norm_value"] = table["norm_fine"].fillna(table["norm_coarse"]).fillna(table["norm_zone"])
    return table[[config.COL_ZONE, "day_of_week", "hour", "norm_value"]]


def prepare_model_input(df: pd.DataFrame, feature_cols=config.FEATURE_COLUMNS) -> pd.DataFrame:
    """The exact feature-encoding step (column selection/order, categorical
    dtype for locationid) shared by training and production serving
    (modeling/predict.py), so the two can never silently drift apart."""
    X = df[feature_cols].copy()
    X[config.COL_ZONE] = X[config.COL_ZONE].astype("category")
    return X


def fit_lightgbm(fit_df: pd.DataFrame, val_df: pd.DataFrame) -> lgb.Booster:
    train_set = lgb.Dataset(
        prepare_model_input(fit_df), label=fit_df["deviation"], categorical_feature=[config.COL_ZONE]
    )
    val_set = lgb.Dataset(
        prepare_model_input(val_df), label=val_df["deviation"], reference=train_set
    )
    params = {**config.LGBM_PARAMS, "objective": "regression", "metric": "mae", "verbosity": -1}
    return lgb.train(
        params,
        train_set,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(config.LGBM_EARLY_STOPPING_ROUNDS), lgb.log_evaluation(0)],
    )


def compute_level_thresholds(trainval_df: pd.DataFrame) -> dict:
    floor = float(trainval_df["busyness_score"].quantile(config.LEVEL_LOW_PERCENTILE))
    ceiling = float(trainval_df["busyness_score"].quantile(config.LEVEL_HIGH_PERCENTILE))
    return {
        "floor": floor,
        "ceiling": ceiling,
        "deadband": config.LEVEL_DEVIATION_DEADBAND,
        "labels": list(config.LEVEL_LABELS),
    }


def train() -> dict:
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = _ym(features[config.COL_HOUR])

    trainval_yms, test_yms = split_months()
    trainval_df = features.loc[features["_ym"].isin(trainval_yms)].copy()
    test_df = features.loc[features["_ym"].isin(test_yms)].copy()

    trainval_df["norm"] = compute_expanding_norms(trainval_df)
    trainval_df["deviation"] = trainval_df["busyness_score"] - trainval_df["norm"]

    fit_df, val_df = split_fit_val(trainval_df)

    norm_table = build_norm_table(trainval_df)
    final_profile = compute_norm_profile(trainval_df)
    test_df["norm"] = apply_norm_profile(test_df, *final_profile).to_numpy()
    test_df["deviation"] = test_df["busyness_score"] - test_df["norm"]

    booster = fit_lightgbm(fit_df, val_df)

    predicted_deviation = booster.predict(prepare_model_input(test_df), num_iteration=booster.best_iteration)
    predicted_busyness = test_df["norm"].to_numpy() + predicted_deviation
    model_mae = mean_absolute_error(test_df["busyness_score"], predicted_busyness)
    baseline_mae = mean_absolute_error(test_df["busyness_score"], test_df["norm"])

    level_thresholds = compute_level_thresholds(trainval_df)

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    # booster.best_iteration does NOT survive a save/load round trip (comes
    # back as -1) - saving only the trees up to best_iteration means the
    # reloaded model is correct on its own, without production code needing
    # to know or persist that number separately.
    booster.save_model(str(config.MODEL_PATH), num_iteration=booster.best_iteration)
    norm_table.to_csv(config.NORM_TABLE_PATH, index=False)
    with open(config.FEATURE_COLS_PATH, "w") as f:
        json.dump(config.FEATURE_COLUMNS, f, indent=2)
    with open(config.LEVEL_THRESHOLDS_PATH, "w") as f:
        json.dump(level_thresholds, f, indent=2)

    return {
        "best_iteration": booster.best_iteration,
        "model_mae": model_mae,
        "baseline_mae": baseline_mae,
        "n_fit": len(fit_df),
        "n_val": len(val_df),
        "n_test": len(test_df),
        "level_thresholds": level_thresholds,
    }
