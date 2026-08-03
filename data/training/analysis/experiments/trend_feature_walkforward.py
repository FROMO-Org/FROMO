"""Walk-forward validation of the months_since_start trend feature: does
its improvement (measured only on May 2026 in
analysis/experiments/trend_feature_test.py, then adopted into the real
pipeline) hold up across OTHER held-out months too, or was it specific to
that one train/test split?

Read-only against the real pipeline and the locked analysis deliverables:
reuses modeling/train.py's own functions (never modifies them), trains
throwaway models in memory, writes no artifact, does not touch
config.py/features.csv/artifacts/.

For each candidate test month, trainval = every month strictly before it
(an expanding window, consistent with how the real pipeline prevents
leakage) - never months after. This is a genuine walk-forward check, not
random cross-validation, since the underlying task is a time-forecasting
one and using future months to predict the past would be leakage.
"""

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import mean_absolute_error

import config
from modeling import train as train_mod

BASELINE_FEATURES = [c for c in config.FEATURE_COLUMNS if c != "months_since_start"]
TREND_FEATURES = config.FEATURE_COLUMNS


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
    return mae, bias


def run_fold(features: pd.DataFrame, test_ym: int, all_yms: list[int]) -> dict:
    trainval_yms = [ym for ym in all_yms if ym < test_ym]
    trainval_df = features.loc[features["_ym"].isin(trainval_yms)].copy()
    test_df = features.loc[features["_ym"] == test_ym].copy()

    trainval_df["norm"] = train_mod.compute_expanding_norms(trainval_df)
    trainval_df["deviation"] = trainval_df["busyness_score"] - trainval_df["norm"]
    fit_df, val_df = train_mod.split_fit_val(trainval_df)

    final_profile = train_mod.compute_norm_profile(trainval_df)
    test_df["norm"] = train_mod.apply_norm_profile(test_df, *final_profile).to_numpy()
    test_df["deviation"] = test_df["busyness_score"] - test_df["norm"]

    baseline_mae, baseline_bias = fit_and_eval(fit_df, val_df, test_df, BASELINE_FEATURES)
    trend_mae, trend_bias = fit_and_eval(fit_df, val_df, test_df, TREND_FEATURES)

    return {
        "test_ym": test_ym,
        "n_trainval_months": len(trainval_yms),
        "baseline_mae": baseline_mae,
        "trend_mae": trend_mae,
        "mae_change_pct": (trend_mae - baseline_mae) / baseline_mae * 100,
        "baseline_bias": baseline_bias,
        "trend_bias": trend_bias,
        "bias_abs_change_pct": (abs(trend_bias) - abs(baseline_bias)) / abs(baseline_bias) * 100,
    }


def run() -> pd.DataFrame:
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = train_mod._ym(features[config.COL_HOUR])

    all_months = config.get_covered_months()
    all_yms = [train_mod._month_ym(y, m) for y, m, _ in all_months]

    n = len(all_yms)
    fold_indices = sorted({int(n * frac) - 1 for frac in (0.5, 0.65, 0.8, 0.9, 1.0)})
    fold_indices = [i for i in fold_indices if i >= n // 3]  # require real prior history
    test_yms = [all_yms[i] for i in fold_indices]

    results = []
    for test_ym in test_yms:
        print(f"--- test month {test_ym} ({sum(1 for y in all_yms if y < test_ym)} prior months) ---")
        result = run_fold(features, test_ym, all_yms)
        print(
            f"  baseline MAE={result['baseline_mae']:.5f}  trend MAE={result['trend_mae']:.5f}  "
            f"change={result['mae_change_pct']:+.1f}%"
        )
        print(
            f"  baseline bias={result['baseline_bias']:+.5f}  trend bias={result['trend_bias']:+.5f}  "
            f"|bias| change={result['bias_abs_change_pct']:+.1f}%"
        )
        results.append(result)

    df = pd.DataFrame(results)
    print()
    print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    run()
