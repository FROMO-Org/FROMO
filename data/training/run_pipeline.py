"""Top-level orchestrator: runs every stage (ingest -> geo/spatial join ->
scoring -> features -> modeling) in order, in one process, so there is no
persistent kernel state to fall out of sync with the code on disk (the
class of reproducibility problem found in the legacy notebooks).

Nothing in this module, writes to any
external database - there is no database client, credential, or connection
of any kind in this codebase. The only writes are local files under
new_pipeline/data/ and new_pipeline/artifacts/. The final step is a
prediction dry run (modeling.predict.predict(dry_run=True)), which makes a
read-only call to the public Open-Meteo forecast API and does not even
write the local predictions CSV unless dry_run=False is passed explicitly.
"""

import logging
import time

import pandas as pd

import config
from features import build_features
from geo import spatial_join, zones
from ingest import bike, subway, taxi
from modeling import predict, train
from scoring import composite, normalize
from validation import checks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_ingest() -> dict:
    bike_frames = []
    taxi_frames = []
    for year, month, tag in config.get_covered_months():
        bike_month = bike.clean_month(year, month, tag)
        checks.assert_no_nulls(bike_month, context=f"bike {tag}")
        bike_frames.append(
            spatial_join.join_points_to_zone_hours(bike_month, source=config.MODE_BIKE)
        )

        taxi_month = taxi.clean_month(year, month, tag)
        checks.assert_no_nulls(taxi_month, context=f"taxi {tag}")
        taxi_frames.append(taxi_month)
    logger.info("Ingested bike + taxi for %d months", len(config.get_covered_months()))

    subway_all = spatial_join.join_points_to_zone_hours(
        subway.clean_all_months(), source=config.MODE_SUBWAY
    )
    logger.info("Ingested subway")

    mode_frames = {
        config.MODE_BIKE: pd.concat(bike_frames, ignore_index=True),
        config.MODE_TAXI: pd.concat(taxi_frames, ignore_index=True),
        config.MODE_SUBWAY: subway_all,
    }
    for mode, df in mode_frames.items():
        checks.assert_unique(df, subset=[config.COL_ZONE, config.COL_HOUR], context=f"{mode} post-join")
    return mode_frames


def run_scoring(mode_frames: dict) -> pd.DataFrame:
    panel = composite.build_wide_panel(mode_frames)

    kept_zone_count = len(zones.get_kept_zone_ids())
    start, end = config.get_full_date_range()
    expected_hours = len(pd.date_range(start, end, freq="h"))
    checks.assert_row_count(panel, kept_zone_count * expected_hours, context="wide panel")
    checks.assert_no_nulls(panel, context="wide panel")

    scored, thresholds = composite.compute_score(panel)
    checks.assert_no_nulls(scored, columns=["busyness_score", "busyness_display"], context="scored panel")
    checks.assert_value_range(scored, "busyness_score", 0.0, 1.0, context="scored panel")
    checks.assert_unique(scored, subset=[config.COL_ZONE, config.COL_HOUR], context="scored panel")

    normalize.save_thresholds(thresholds)
    config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    scored.to_csv(config.BUSYNESS_SCORED_PATH, index=False)
    logger.info("Saved scored panel: %s (%d rows)", config.BUSYNESS_SCORED_PATH, len(scored))
    return scored


def run_features(scored: pd.DataFrame) -> pd.DataFrame:
    features = build_features.build_features(scored)
    checks.assert_no_nulls(features, context="features")
    checks.assert_columns_present(
        features,
        [config.COL_ZONE, config.COL_HOUR, "busyness_score"] + config.FEATURE_COLUMNS,
        context="features",
    )
    checks.assert_unique(features, subset=[config.COL_ZONE, config.COL_HOUR], context="features")

    features.to_csv(config.FEATURES_PATH, index=False)
    logger.info("Saved features: %s (%d rows)", config.FEATURES_PATH, len(features))
    return features


def run_model() -> dict:
    result = train.train()
    logger.info("Model trained: %s", result)
    return result


def run_prediction_smoke_test() -> pd.DataFrame:
    """A read-only check that the trained model produces sane predictions
    end-to-end, including a live weather-forecast fetch. Writes nothing -
    dry_run defaults to True and there is no database write path to begin
    with anywhere in this codebase."""
    result = predict.predict(dry_run=True)
    checks.assert_no_nulls(result, context="predictions")
    logger.info(
        "Prediction dry run: %d rows, level distribution %s",
        len(result),
        result["level"].value_counts().to_dict(),
    )
    return result


def run_pipeline() -> dict:
    t0 = time.time()
    mode_frames = run_ingest()
    scored = run_scoring(mode_frames)
    features = run_features(scored)
    model_result = run_model()
    prediction_preview = run_prediction_smoke_test()

    elapsed = time.time() - t0
    logger.info("Pipeline completed in %.1fs", elapsed)
    return {
        "scored_rows": len(scored),
        "feature_rows": len(features),
        "model_result": model_result,
        "prediction_rows": len(prediction_preview),
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    run_pipeline()
