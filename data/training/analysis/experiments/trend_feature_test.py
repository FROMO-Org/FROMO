"""Experiment (not part of the pipeline or the locked analysis deliverables
- read-only against both): does an explicit trend feature ("months since
the start of the training window") reduce the systematic over-prediction
bias found in analysis/model_errors.py?

Trains two throwaway models in memory using the exact same data,
norm-computation, and fit/val split as modeling/train.py (reusing its
functions directly, not reimplementing them) - one with the current 9
features, one with a 10th "months_since_start" feature added. Neither
model is saved to artifacts/; config.py, features.csv, and the production
model.txt/norm_table.csv/feature_cols.json are never written to.
"""

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import mean_absolute_error

import config
from modeling import train as train_mod


def add_trend_feature(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    start_year, start_month, _ = config.get_covered_months()[0]
    df["months_since_start"] = (df[config.COL_HOUR].dt.year - start_year) * 12 + (
        df[config.COL_HOUR].dt.month - start_month
    )
    return df


def fit_and_eval(fit_df, val_df, test_df, feature_cols):
    train_set = lgb.Dataset(
        train_mod.prepare_model_input(fit_df, feature_cols=feature_cols),
        label=fit_df["deviation"],
        categorical_feature=[config.COL_ZONE],
    )
    val_set = lgb.Dataset(
        train_mod.prepare_model_input(val_df, feature_cols=feature_cols),
        label=val_df["deviation"],
        reference=train_set,
    )
    params = {**config.LGBM_PARAMS, "objective": "regression", "metric": "mae", "verbosity": -1}
    booster = lgb.train(
        params,
        train_set,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(config.LGBM_EARLY_STOPPING_ROUNDS), lgb.log_evaluation(0)],
    )
    pred_dev = booster.predict(train_mod.prepare_model_input(test_df, feature_cols=feature_cols))
    pred_busy = test_df["norm"].to_numpy() + pred_dev
    mae = mean_absolute_error(test_df["busyness_score"], pred_busy)
    bias = (test_df["busyness_score"].to_numpy() - pred_busy).mean()
    return mae, bias, booster


def run_experiment():
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = train_mod._ym(features[config.COL_HOUR])
    features = add_trend_feature(features)

    trainval_yms, test_yms = train_mod.split_months()
    trainval_df = features.loc[features["_ym"].isin(trainval_yms)].copy()
    test_df = features.loc[features["_ym"].isin(test_yms)].copy()

    trainval_df["norm"] = train_mod.compute_expanding_norms(trainval_df)
    trainval_df["deviation"] = trainval_df["busyness_score"] - trainval_df["norm"]
    fit_df, val_df = train_mod.split_fit_val(trainval_df)

    final_profile = train_mod.compute_norm_profile(trainval_df)
    test_df["norm"] = train_mod.apply_norm_profile(test_df, *final_profile).to_numpy()
    test_df["deviation"] = test_df["busyness_score"] - test_df["norm"]

    baseline_cols = config.FEATURE_COLUMNS
    trend_cols = config.FEATURE_COLUMNS + ["months_since_start"]

    baseline_mae, baseline_bias, _ = fit_and_eval(fit_df, val_df, test_df, baseline_cols)
    trend_mae, trend_bias, trend_booster = fit_and_eval(fit_df, val_df, test_df, trend_cols)

    print(f"Baseline (9 features):         MAE={baseline_mae:.5f}  bias={baseline_bias:+.5f}")
    print(f"With months_since_start (10):  MAE={trend_mae:.5f}  bias={trend_bias:+.5f}")
    print(f"MAE change:  {(trend_mae - baseline_mae) / baseline_mae:+.2%}")
    print(f"|bias| change: {(abs(trend_bias) - abs(baseline_bias)) / abs(baseline_bias):+.2%}")

    importance = pd.Series(
        trend_booster.feature_importance(importance_type="gain"), index=trend_cols
    ).sort_values(ascending=False)
    print()
    print("Feature importance (gain), model with trend feature:")
    print(importance.to_string())


if __name__ == "__main__":
    run_experiment()
