"""Model-comparison step: trains several alternative regressors on the
exact same leakage-safe target, split, and feature set that
modeling/train.py uses for the production LightGBM model, to produce an
honest comparison table justifying LightGBM's selection.

Reuses modeling.train's own split/target functions directly
(split_months, split_fit_val, compute_expanding_norms,
compute_norm_profile, apply_norm_profile, prepare_model_input) rather than
reimplementing them. This matters specifically for the training target:
the model predicts deviation from an EXPANDING-WINDOW norm (only strictly
prior months contribute to each training month's norm), not the static
full-training-window profile in norm_table.csv - that static table is only
a valid stand-in at production predict time, where the target month is
chronologically after every training month. Computing every model's
training target from the static profile instead would leak future months
into earlier months' "expected" value and make every model here look
artificially better than the real pipeline; reusing train.py's own
functions makes that bug structurally impossible rather than something to
remember not to do.

This module is purely additive: it reads data/processed/features.csv and
writes only artifacts/model_comparison.{csv,json}. It never touches
busyness_score, norm_table.csv, level_thresholds.json, or the production
model.txt - every model trained here is discarded after evaluation, except
that the production model.txt IS reloaded (read-only) as the ground truth
for the correctness check below.

Correctness check: LightGBM is retrained here via train.py's own
fit_lightgbm(), on the identical fit_df/val_df this module reconstructs.
If the reconstruction is faithful, this freshly-trained model's test MAE
must land close to the real production model's test MAE (obtained by
reloading artifacts/model.txt - already trained by the real
run_pipeline.py - and evaluating it on the same reconstructed test set).
A large divergence here means the split/target reconstruction is wrong,
and run_comparison() raises rather than silently reporting a bogus table.
"""

import json
import logging
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config
from modeling import train as train_mod

# Random Forest is by far the most compute-heavy model on ~690k rows; capped
# (rather than sklearn's unbounded defaults) so a single comparison run
# finishes in a reasonable time. If this still turns out to be slow, that
# compute cost is itself the reportable finding (see fit_seconds column),
# not a reason to silently shrink the config further.
RF_N_ESTIMATORS = 100
RF_MAX_DEPTH = 14

# LightGBM/XGBoost retrained here vs. the real production model.txt should
# land within this relative tolerance if the split/target reconstruction is
# faithful. Generous on purpose: it only needs to catch gross reconstruction
# bugs (e.g. leakage from a static norm), which shift MAE by a large margin,
# not ordinary run-to-run training noise.
PRODUCTION_MATCH_RTOL = 0.15

COMPARISON_CSV_PATH = config.ARTIFACTS_DIR / "model_comparison.csv"
COMPARISON_JSON_PATH = config.ARTIFACTS_DIR / "model_comparison.json"

logger = logging.getLogger(__name__)


def _prepare_split():
    """Reconstruct train.py's exact fit_df/val_df/test_df, with the same
    expanding-window training target and static-profile test target, by
    calling train.py's own functions directly (see module docstring)."""
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = train_mod._ym(features[config.COL_HOUR])

    trainval_yms, test_yms = train_mod.split_months()
    trainval_df = features.loc[features["_ym"].isin(trainval_yms)].copy()
    test_df = features.loc[features["_ym"].isin(test_yms)].copy()

    trainval_df["norm"] = train_mod.compute_expanding_norms(trainval_df)
    trainval_df["deviation"] = trainval_df["busyness_score"] - trainval_df["norm"]

    fit_df, val_df = train_mod.split_fit_val(trainval_df)

    final_profile = train_mod.compute_norm_profile(trainval_df)
    test_df["norm"] = train_mod.apply_norm_profile(test_df, *final_profile).to_numpy()
    test_df["deviation"] = test_df["busyness_score"] - test_df["norm"]

    return fit_df, val_df, test_df


def _score(name, predicted_deviation, test_df, fit_seconds):
    """One comparison-table row: MAE/R2/bias on the reconstructed busyness
    scale (norm added back), directly comparable to the pipeline's own
    reported test MAE."""
    predicted_deviation = np.asarray(predicted_deviation, dtype=float)
    predicted_busyness = test_df["norm"].to_numpy() + predicted_deviation
    actual_busyness = test_df["busyness_score"].to_numpy()

    return {
        "model": name,
        "test_mae": mean_absolute_error(actual_busyness, predicted_busyness),
        "r2_deviation": r2_score(test_df["deviation"].to_numpy(), predicted_deviation),
        "bias": float(np.mean(predicted_busyness - actual_busyness)),
        "fit_seconds": fit_seconds,
    }


def _baseline_trust_norm(test_df):
    return _score("trust_the_norm", np.zeros(len(test_df)), test_df, fit_seconds=0.0)


def _baseline_zone_bias(fit_df, test_df):
    t0 = time.perf_counter()
    zone_bias = fit_df.groupby(config.COL_ZONE)["deviation"].mean()
    global_bias = fit_df["deviation"].mean()
    fit_seconds = time.perf_counter() - t0

    predicted = test_df[config.COL_ZONE].map(zone_bias).fillna(global_bias).to_numpy()
    return _score("per_zone_mean_bias", predicted, test_df, fit_seconds)


def _ridge_pipeline():
    numeric_cols = [c for c in config.FEATURE_COLUMNS if c != config.COL_ZONE]
    preprocessor = ColumnTransformer(
        [
            ("zone_ohe", OneHotEncoder(handle_unknown="ignore"), [config.COL_ZONE]),
            ("scale", StandardScaler(), numeric_cols),
        ]
    )
    return Pipeline([("preprocess", preprocessor), ("ridge", Ridge(alpha=1.0))])


def _fit_ridge(fit_df, test_df):
    X_fit = fit_df[config.FEATURE_COLUMNS]
    y_fit = fit_df["deviation"]
    X_test = test_df[config.FEATURE_COLUMNS]

    model = _ridge_pipeline()
    t0 = time.perf_counter()
    model.fit(X_fit, y_fit)
    fit_seconds = time.perf_counter() - t0

    predicted = model.predict(X_test)
    return _score("ridge", predicted, test_df, fit_seconds)


def _fit_xgboost(fit_df, val_df, test_df):
    X_fit = train_mod.prepare_model_input(fit_df)
    X_val = train_mod.prepare_model_input(val_df)
    X_test = train_mod.prepare_model_input(test_df)

    model = xgb.XGBRegressor(
        n_estimators=config.LGBM_PARAMS["n_estimators"],
        learning_rate=config.LGBM_PARAMS["learning_rate"],
        max_leaves=config.LGBM_PARAMS["num_leaves"],
        grow_policy="lossguide",
        tree_method="hist",
        min_child_weight=config.LGBM_PARAMS["min_child_samples"],
        enable_categorical=True,
        random_state=config.RANDOM_STATE,
        early_stopping_rounds=config.LGBM_EARLY_STOPPING_ROUNDS,
        eval_metric="mae",
        n_jobs=-1,
    )

    t0 = time.perf_counter()
    model.fit(X_fit, fit_df["deviation"], eval_set=[(X_val, val_df["deviation"])], verbose=False)
    fit_seconds = time.perf_counter() - t0

    predicted = model.predict(X_test)
    return _score("xgboost", predicted, test_df, fit_seconds)


def _random_forest_pipeline():
    numeric_cols = [c for c in config.FEATURE_COLUMNS if c != config.COL_ZONE]
    preprocessor = ColumnTransformer(
        [
            ("zone_ohe", OneHotEncoder(handle_unknown="ignore"), [config.COL_ZONE]),
            ("passthrough", "passthrough", numeric_cols),
        ]
    )
    rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        n_jobs=-1,
        random_state=config.RANDOM_STATE,
    )
    return Pipeline([("preprocess", preprocessor), ("rf", rf)])


def _fit_random_forest(fit_df, test_df):
    X_fit = fit_df[config.FEATURE_COLUMNS]
    y_fit = fit_df["deviation"]
    X_test = test_df[config.FEATURE_COLUMNS]

    model = _random_forest_pipeline()
    t0 = time.perf_counter()
    model.fit(X_fit, y_fit)
    fit_seconds = time.perf_counter() - t0
    logger.info(
        "Random Forest fit in %.1fs (n_estimators=%d, max_depth=%d, n_jobs=-1) on %d rows",
        fit_seconds, RF_N_ESTIMATORS, RF_MAX_DEPTH, len(fit_df),
    )

    predicted = model.predict(X_test)
    return _score("random_forest", predicted, test_df, fit_seconds)


def _fit_lightgbm_reproduced(fit_df, val_df, test_df):
    """Retrains LightGBM here via train.py's own fit_lightgbm(), on the
    identical fit_df/val_df and config.LGBM_PARAMS. Not saved anywhere -
    this is a throwaway model, purely for the comparison table and the
    correctness check against the real production model.txt."""
    t0 = time.perf_counter()
    booster = train_mod.fit_lightgbm(fit_df, val_df)
    fit_seconds = time.perf_counter() - t0

    X_test = train_mod.prepare_model_input(test_df)
    predicted = booster.predict(X_test, num_iteration=booster.best_iteration)
    row = _score("lightgbm", predicted, test_df, fit_seconds)
    row["best_iteration"] = booster.best_iteration
    return row


def _verify_against_production(reproduced_test_mae, test_df):
    """Loads the real production model.txt (read-only - never rewritten
    here) and evaluates it on this module's own reconstructed test_df. If
    _prepare_split() faithfully reproduces train.py's target/split, this
    number and the freshly-retrained LightGBM's test MAE must be close;
    a large gap means the reconstruction is wrong (most likely: training
    target leaked future months via a non-expanding norm), and this raises
    rather than letting a bogus comparison table through."""
    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(
            f"{config.MODEL_PATH} not found - run modeling.train.train() "
            "(or run_pipeline.py) before modeling.compare.run_comparison()."
        )

    booster = lgb.Booster(model_file=str(config.MODEL_PATH))
    X_test = train_mod.prepare_model_input(test_df)
    predicted = booster.predict(X_test)
    production_row = _score("lightgbm_production_reloaded", predicted, test_df, fit_seconds=None)
    production_mae = production_row["test_mae"]

    rel_diff = abs(reproduced_test_mae - production_mae) / production_mae
    passed = rel_diff <= PRODUCTION_MATCH_RTOL
    logger.info(
        "Correctness check: reproduced LightGBM test MAE=%.6f vs. reloaded "
        "production model.txt test MAE=%.6f (relative diff %.1f%%, tolerance %.0f%%) -> %s",
        reproduced_test_mae, production_mae, rel_diff * 100, PRODUCTION_MATCH_RTOL * 100,
        "PASS" if passed else "FAIL",
    )
    if not passed:
        raise RuntimeError(
            f"modeling.compare's reconstructed test MAE ({reproduced_test_mae:.6f}) diverges "
            f"from the real production model.txt's test MAE ({production_mae:.6f}) by "
            f"{rel_diff:.1%}, exceeding the {PRODUCTION_MATCH_RTOL:.0%} tolerance. This means "
            "_prepare_split() is not faithfully reproducing modeling.train's target/split "
            "(e.g. the training target may be leaking future months) - diagnose before "
            "trusting any row in the comparison table."
        )
    return production_mae


def run_comparison() -> pd.DataFrame:
    fit_df, val_df, test_df = _prepare_split()
    logger.info(
        "Model comparison split: n_fit=%d, n_val=%d, n_test=%d", len(fit_df), len(val_df), len(test_df)
    )

    rows = [
        _baseline_trust_norm(test_df),
        _baseline_zone_bias(fit_df, test_df),
        _fit_ridge(fit_df, test_df),
        _fit_xgboost(fit_df, val_df, test_df),
        _fit_lightgbm_reproduced(fit_df, val_df, test_df),
        _fit_random_forest(fit_df, test_df),
    ]

    lightgbm_row = next(r for r in rows if r["model"] == "lightgbm")
    _verify_against_production(lightgbm_row["test_mae"], test_df)

    result = pd.DataFrame(rows)
    trust_norm_mae = result.loc[result["model"] == "trust_the_norm", "test_mae"].iloc[0]
    result["improvement_pct_vs_trust_norm"] = (
        (trust_norm_mae - result["test_mae"]) / trust_norm_mae * 100
    )
    result = result.sort_values("test_mae").reset_index(drop=True)

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(COMPARISON_CSV_PATH, index=False)
    with open(COMPARISON_JSON_PATH, "w") as f:
        json.dump(result.to_dict(orient="records"), f, indent=2)
    logger.info("Saved model comparison: %s", COMPARISON_CSV_PATH)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    df = run_comparison()
    print(df.to_string(index=False))
