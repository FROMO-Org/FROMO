"""Model error analysis: where does the trained model's held-out test-month
prediction perform worst, by zone / hour / day-of-week / holiday / weather?
Read-only diagnostic - loads the already-trained artifacts and the already
-built features table, does not retrain or modify anything.

Reuses modeling/train.py's own split/prepare functions so "the test set"
here is identically defined to the one train.py evaluated against - this is
a deeper look at the same numbers, not a different evaluation.
"""

import json

import lightgbm as lgb
import pandas as pd

import config
from geo import zones
from modeling import train as train_mod


def load_test_predictions() -> pd.DataFrame:
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    features["_ym"] = train_mod._ym(features[config.COL_HOUR])
    _, test_yms = train_mod.split_months()
    test_df = features.loc[features["_ym"].isin(test_yms)].copy()

    booster = lgb.Booster(model_file=str(config.MODEL_PATH))
    norm_table = pd.read_csv(config.NORM_TABLE_PATH).rename(columns={"norm_value": "norm"})
    with open(config.FEATURE_COLS_PATH) as f:
        feature_cols = json.load(f)

    test_df = test_df.merge(norm_table, on=[config.COL_ZONE, "day_of_week", "hour"], how="left")
    X = train_mod.prepare_model_input(test_df, feature_cols=feature_cols)
    predicted_deviation = booster.predict(X)
    test_df["predicted_busyness"] = test_df["norm"] + predicted_deviation
    test_df["residual"] = test_df["busyness_score"] - test_df["predicted_busyness"]
    test_df["abs_error"] = test_df["residual"].abs()
    return test_df


def summarize(test_df: pd.DataFrame) -> dict:
    zone_names = zones.get_kept_zones().set_index(config.ZONE_ID_COLUMN)["zone"]

    by_zone_error = test_df.groupby(config.COL_ZONE)["abs_error"].mean().rename("mae")
    by_zone_bias = test_df.groupby(config.COL_ZONE)["residual"].mean().rename("mean_residual")
    by_zone = pd.concat([by_zone_error, by_zone_bias], axis=1)
    by_zone["zone_name"] = by_zone.index.map(zone_names)
    by_zone = by_zone.sort_values("mae", ascending=False)

    by_hour = test_df.groupby("hour")["abs_error"].mean().sort_values(ascending=False)
    by_dow = test_df.groupby("day_of_week")["abs_error"].mean().sort_values(ascending=False)
    by_holiday = test_df.groupby("is_holiday")["abs_error"].mean()

    weather_corr = test_df[
        ["abs_error", "temperature", "apparent_temperature", "precipitation", "snowfall"]
    ].corr()["abs_error"].drop("abs_error")

    return {
        "overall_mae": test_df["abs_error"].mean(),
        "overall_bias": test_df["residual"].mean(),
        "by_zone": by_zone,
        "by_hour": by_hour,
        "by_dow": by_dow,
        "by_holiday": by_holiday,
        "weather_corr": weather_corr,
    }


if __name__ == "__main__":
    test_df = load_test_predictions()
    summary = summarize(test_df)

    print("Overall test MAE:", summary["overall_mae"])
    print("Overall test bias (mean residual):", summary["overall_bias"])
    print()
    print("Worst 15 zones by MAE:")
    print(summary["by_zone"].head(15).to_string())
    print()
    print("Best 15 zones by MAE:")
    print(summary["by_zone"].tail(15).to_string())
    print()
    print("Most under-predicted zones (model predicts too LOW, mean_residual > 0):")
    print(summary["by_zone"].sort_values("mean_residual", ascending=False).head(10).to_string())
    print()
    print("Most over-predicted zones (model predicts too HIGH, mean_residual < 0):")
    print(summary["by_zone"].sort_values("mean_residual").head(10).to_string())
    print()
    print("MAE by hour of day:")
    print(summary["by_hour"].to_string())
    print()
    print("MAE by day of week (0=Mon..6=Sun):")
    print(summary["by_dow"].to_string())
    print()
    print("MAE by is_holiday:")
    print(summary["by_holiday"].to_string())
    print()
    print("Correlation of abs_error with weather features:")
    print(summary["weather_corr"].to_string())

    out_path = config.DATA_PROCESSED_DIR / "test_residuals.csv"
    test_df.to_csv(out_path, index=False)
    print()
    print("Saved per-row residuals to", out_path)
