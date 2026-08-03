"""Model-interpretability visualizations for the production model
(artifacts/model.txt) - feature importance and SHAP values - describing
the model actually being deployed, not a freshly retrained stand-in.

Reuses modeling.train's own month-split and feature-encoding functions
(split_months, prepare_model_input, and config.FEATURE_COLUMNS - the same
9 features and locationid categorical handling in artifacts/feature_cols.json)
rather than reimplementing them, so importances/SHAP values are computed
against the exact same feature set, ordering, and encoding the model was
trained and is served with (modeling/predict.py uses this same
prepare_model_input for live inference). Computed on the held-out test
month - the most recent TEST_HOLDOUT_MONTHS discovered months, the same
rows the pipeline's own reported test MAE is computed on - not the
training data, so the figures reflect the model's behavior on data it did
not fit.

Read-only against the model: loads artifacts/model.txt via
lgb.Booster(model_file=...) and never retrains or resaves it. Writes only
new files under artifacts/ (feature_importance.csv) and artifacts/figures/
- never touches model.txt, busyness_score, norm_table.csv,
level_thresholds.json, or any other production artifact.

Run standalone: `python -m modeling.interpret`. Not wired into
run_pipeline.py - like modeling/compare.py, this is a run-once, on-demand
step, not part of every pipeline run.
"""

import logging

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

import config
from modeling import train as train_mod

RANDOM_STATE = config.RANDOM_STATE
# Full test month is 49,104 rows - too dense to render as a readable
# beeswarm. Sampled down to a fixed-seed representative subset instead.
SHAP_SAMPLE_SIZE = 5000

FIGURES_DIR = config.ARTIFACTS_DIR / "figures"
FEATURE_IMPORTANCE_CSV_PATH = config.ARTIFACTS_DIR / "feature_importance.csv"
FEATURE_IMPORTANCE_FIG_PATH = FIGURES_DIR / "feature_importance.png"
SHAP_SUMMARY_FIG_PATH = FIGURES_DIR / "shap_summary.png"
SHAP_BAR_FIG_PATH = FIGURES_DIR / "shap_bar.png"

logger = logging.getLogger(__name__)


def load_production_model() -> lgb.Booster:
    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(
            f"{config.MODEL_PATH} not found - run modeling.train.train() "
            "(or run_pipeline.py) before modeling.interpret."
        )
    return lgb.Booster(model_file=str(config.MODEL_PATH))


def load_test_features() -> pd.DataFrame:
    """The held-out test month's rows (features.csv filtered to
    train.py's own split_months()'s test_yms), encoded via train.py's own
    prepare_model_input - the exact same encoding used for training and
    production serving in modeling/predict.py."""
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = train_mod._ym(features[config.COL_HOUR])
    _, test_yms = train_mod.split_months()
    test_df = features.loc[features["_ym"].isin(test_yms)].copy()
    return train_mod.prepare_model_input(test_df)


def compute_feature_importance(booster: lgb.Booster) -> pd.DataFrame:
    return (
        pd.DataFrame(
            {
                "feature": booster.feature_name(),
                "split": booster.feature_importance(importance_type="split"),
                "gain": booster.feature_importance(importance_type="gain"),
            }
        )
        .sort_values("gain", ascending=False)
        .reset_index(drop=True)
    )


def plot_feature_importance(importance_df: pd.DataFrame, path) -> None:
    ordered = importance_df.sort_values("gain", ascending=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    axes[0].barh(ordered["feature"], ordered["gain"], color="#4C72B0")
    axes[0].set_title("Importance by gain")
    axes[0].set_xlabel("Total gain")

    axes[1].barh(ordered["feature"], ordered["split"], color="#DD8452")
    axes[1].set_title("Importance by split count")
    axes[1].set_xlabel("Number of splits")

    fig.suptitle("LightGBM feature importance (production model.txt)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def compute_shap_values(booster: lgb.Booster, X: pd.DataFrame):
    sample_size = min(SHAP_SAMPLE_SIZE, len(X))
    X_sample = X.sample(n=sample_size, random_state=RANDOM_STATE)
    explainer = shap.TreeExplainer(booster)
    shap_values = explainer.shap_values(X_sample)
    return X_sample, shap_values


def plot_shap_summary(X_sample, shap_values, path) -> None:
    plt.figure()
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_shap_bar(X_sample, shap_values, path) -> None:
    plt.figure()
    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def mean_abs_shap(X_sample: pd.DataFrame, shap_values) -> pd.DataFrame:
    mean_abs = np.abs(shap_values).mean(axis=0)
    return (
        pd.DataFrame({"feature": X_sample.columns, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )


def run_interpretation() -> dict:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    booster = load_production_model()
    X_test = load_test_features()
    logger.info("Loaded production model.txt + %d held-out test-month rows", len(X_test))

    importance_df = compute_feature_importance(booster)
    importance_df.to_csv(FEATURE_IMPORTANCE_CSV_PATH, index=False)
    plot_feature_importance(importance_df, FEATURE_IMPORTANCE_FIG_PATH)
    logger.info("Saved %s, %s", FEATURE_IMPORTANCE_CSV_PATH, FEATURE_IMPORTANCE_FIG_PATH)

    X_sample, shap_values = compute_shap_values(booster, X_test)
    logger.info(
        "Computed SHAP values (TreeExplainer) on %d/%d test-month rows (seed=%d)",
        len(X_sample), len(X_test), RANDOM_STATE,
    )
    plot_shap_summary(X_sample, shap_values, SHAP_SUMMARY_FIG_PATH)
    plot_shap_bar(X_sample, shap_values, SHAP_BAR_FIG_PATH)
    logger.info("Saved %s, %s", SHAP_SUMMARY_FIG_PATH, SHAP_BAR_FIG_PATH)

    shap_df = mean_abs_shap(X_sample, shap_values)

    print("\nTop features by gain:")
    print(importance_df[["feature", "gain", "split"]].to_string(index=False))
    print("\nTop features by mean |SHAP|:")
    print(shap_df.to_string(index=False))

    return {"importance": importance_df, "shap": shap_df}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    run_interpretation()
