"""Persists every currently-console-only paper number to
artifacts/paper_stats/. Purely additive: computes nothing that isn't
already computed by analysis/model_errors.py or modeling/interpret.py -
imports and calls their existing functions directly rather than
reimplementing any of the breakdowns, so every persisted number is
guaranteed identical to what those modules already produce.

Despite the name, this does NOT require data/processed/test_residuals.csv
to already exist: analysis.model_errors.load_test_predictions() recomputes
the test-month predictions directly from artifacts/model.txt,
data/processed/features.csv, artifacts/norm_table.csv, and
artifacts/feature_cols.json (all produced by a normal `python
run_pipeline.py` run) - test_residuals.csv is that module's own *output*,
not an input this script needs. Those four artifacts are this script's
real prerequisites, checked up front with a clear error message.

Run standalone: `python -m analysis.export_paper_stats`. Not wired into
run_pipeline.py - like modeling/compare.py, modeling/interpret.py, and
modeling/plot_maps.py, this is a run-once, on-demand step.
"""

import json
import logging

import pandas as pd

import config
from analysis import model_errors
from geo import spatial_join, zones
from ingest import bike, subway, taxi
from modeling import interpret
from modeling import train as train_mod

PAPER_STATS_DIR = config.ARTIFACTS_DIR / "paper_stats"

REQUIRED_ARTIFACTS = [
    config.MODEL_PATH,
    config.FEATURES_PATH,
    config.NORM_TABLE_PATH,
    config.FEATURE_COLS_PATH,
]

logger = logging.getLogger(__name__)


def _require_pipeline_artifacts() -> None:
    missing = [p for p in REQUIRED_ARTIFACTS if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required artifact(s) needed to compute paper stats: "
            + ", ".join(str(p) for p in missing)
            + ". These are produced by a normal pipeline run - run `python "
            "run_pipeline.py` first, then re-run this script."
        )


def export_error_breakdowns(test_df: pd.DataFrame, summary: dict) -> dict:
    """Writes error_by_{zone,hour,dayofweek,holiday}.csv from
    analysis.model_errors.summarize()'s own output - only an `n` (row
    count) column is added here per group, via a plain groupby().size() on
    the same test_df, not a second computation of any error/bias number."""
    zone_counts = test_df.groupby(config.COL_ZONE).size().rename("n")
    by_zone = summary["by_zone"].join(zone_counts).reset_index()
    by_zone = by_zone.rename(columns={"mean_residual": "bias"})
    by_zone = by_zone[[config.COL_ZONE, "zone_name", "mae", "bias", "n"]]
    by_zone = by_zone.sort_values("mae", ascending=False)
    by_zone_path = PAPER_STATS_DIR / "error_by_zone.csv"
    by_zone.to_csv(by_zone_path, index=False)

    hour_counts = test_df.groupby("hour").size().rename("n")
    by_hour = summary["by_hour"].rename("mae").to_frame().join(hour_counts).reset_index()
    by_hour_path = PAPER_STATS_DIR / "error_by_hour.csv"
    by_hour.to_csv(by_hour_path, index=False)

    dow_counts = test_df.groupby("day_of_week").size().rename("n")
    by_dow = summary["by_dow"].rename("mae").to_frame().join(dow_counts).reset_index()
    by_dow_path = PAPER_STATS_DIR / "error_by_dayofweek.csv"
    by_dow.to_csv(by_dow_path, index=False)

    holiday_counts = test_df.groupby("is_holiday").size().rename("n")
    by_holiday = summary["by_holiday"].rename("mae").to_frame().join(holiday_counts).reset_index()
    by_holiday_path = PAPER_STATS_DIR / "error_by_holiday.csv"
    by_holiday.to_csv(by_holiday_path, index=False)

    return {
        "by_zone": (by_zone_path, by_zone),
        "by_hour": (by_hour_path, by_hour),
        "by_dow": (by_dow_path, by_dow),
        "by_holiday": (by_holiday_path, by_holiday),
    }


def export_shap_importance() -> tuple:
    """Reuses modeling.interpret's own model-loading, test-feature-loading,
    SHAP-computation, and aggregation functions directly - no SHAP value is
    computed a second, independent way here."""
    booster = interpret.load_production_model()
    X_test = interpret.load_test_features()
    X_sample, shap_values = interpret.compute_shap_values(booster, X_test)
    shap_df = interpret.mean_abs_shap(X_sample, shap_values)
    path = PAPER_STATS_DIR / "shap_importance.csv"
    shap_df.to_csv(path, index=False)
    return path, shap_df


def _per_mode_raw_totals() -> dict:
    """The exact totals ingest computes. Read from busyness_scored.csv when
    available - its {mode}_count columns ARE ingest's per-(zone,hour)
    output, already left-joined onto the full zero-filled panel by
    scoring/composite.py:build_wide_panel(), so summing them recovers the
    identical total ingest itself produced, without a several-minute full
    re-ingest. Falls back to actually re-running the same ingest functions
    run_pipeline.py uses only if that file isn't present."""
    if config.BUSYNESS_SCORED_PATH.exists():
        cols = [config.count_column(m) for m in config.MODES]
        scored = pd.read_csv(config.BUSYNESS_SCORED_PATH, usecols=cols)
        return {m: float(scored[config.count_column(m)].sum()) for m in config.MODES}

    logger.info(
        "%s not found - recomputing per-mode raw totals via the same ingest "
        "functions run_pipeline.py uses (this re-runs full ingest, several minutes)",
        config.BUSYNESS_SCORED_PATH,
    )
    bike_frames, taxi_frames = [], []
    for year, month, tag in config.get_covered_months():
        bike_frames.append(
            spatial_join.join_points_to_zone_hours(bike.clean_month(year, month, tag), source=config.MODE_BIKE)
        )
        taxi_frames.append(taxi.clean_month(year, month, tag))
    subway_all = spatial_join.join_points_to_zone_hours(subway.clean_all_months(), source=config.MODE_SUBWAY)
    mode_frames = {
        config.MODE_BIKE: pd.concat(bike_frames, ignore_index=True),
        config.MODE_TAXI: pd.concat(taxi_frames, ignore_index=True),
        config.MODE_SUBWAY: subway_all,
    }
    return {m: float(df[config.COL_COUNT].sum()) for m, df in mode_frames.items()}


def export_dataset_manifest() -> tuple:
    """Every value here is derived at runtime from the same functions the
    rest of the pipeline uses (train.py's own split, geo.zones, config's
    own date-range function) - nothing is a typed-in literal."""
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    total_feature_rows = len(features)

    features["_ym"] = train_mod._ym(features[config.COL_HOUR])
    trainval_yms, test_yms = train_mod.split_months()
    trainval_df = features.loc[features["_ym"].isin(trainval_yms)]
    test_rows = features.loc[features["_ym"].isin(test_yms)]
    fit_df, val_df = train_mod.split_fit_val(trainval_df)

    n_zones = len(zones.get_kept_zone_ids())
    start, end = config.get_full_date_range()

    manifest = {
        "total_feature_rows": total_feature_rows,
        "n_fit": len(fit_df),
        "n_val": len(val_df),
        "n_test": len(test_rows),
        "n_zones": n_zones,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "per_mode_raw_totals": _per_mode_raw_totals(),
    }
    path = PAPER_STATS_DIR / "dataset_manifest.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return path, manifest


def run_export() -> dict:
    _require_pipeline_artifacts()
    PAPER_STATS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Computing test-month error breakdowns via analysis.model_errors...")
    test_df = model_errors.load_test_predictions()
    summary = model_errors.summarize(test_df)
    breakdowns = export_error_breakdowns(test_df, summary)

    logger.info("Computing SHAP importance via modeling.interpret...")
    shap_path, shap_df = export_shap_importance()

    logger.info("Computing dataset manifest...")
    manifest_path, manifest = export_dataset_manifest()

    written = [path for path, _ in breakdowns.values()] + [shap_path, manifest_path]

    print("\nWrote:")
    for p in written:
        print(" -", p)

    print(f"\nOverall test MAE: {summary['overall_mae']:.6f}   bias: {summary['overall_bias']:.6f}")

    print("\nWorst 5 zones by MAE:")
    print(breakdowns["by_zone"][1].head(5).to_string(index=False))

    print("\nHoliday vs non-holiday MAE:")
    print(breakdowns["by_holiday"][1].to_string(index=False))

    print("\nTop 5 features by mean |SHAP|:")
    print(shap_df.head(5).to_string(index=False))

    print("\nDataset manifest:")
    print(json.dumps(manifest, indent=2))

    return {"written": written, "summary": summary, "breakdowns": breakdowns, "shap": shap_df, "manifest": manifest}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    run_export()
