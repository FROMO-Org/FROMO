"""
Smoke test for predictions.py's core prediction path.

Runs predict() -> apply_norm() -> compute_level() against a tiny, hand-built
fixture (a handful of hours for one zone already covered by norm_table.csv)
and checks the output is well-formed. Does not call fetch_weather() (no
network) or map_area_ids()/push_predictions() (no Supabase) — intentionally
scoped to the offline part of the pipeline so CI never needs secrets or a
live network call.
"""
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DATA_DIR))

import predictions as pred  # noqa: E402


def _fixture_pipeline_df():
    """6 hours for locationid=4 (present in norm_table.csv), with all 9
    feature columns already filled in — stands in for what fetch_weather()
    + generate_tomorrow_calendar() would normally produce."""
    return pd.DataFrame({
        "date": pd.Timestamp("2026-01-15"),
        "locationid": 4,
        "hour": [0, 6, 9, 12, 18, 21],
        "day_of_week": 3,
        "month": 1,
        "is_holiday": False,
        "temperature": [2.0, 3.5, 5.0, 6.5, 4.0, 2.5],
        "apparent_temperature": [-1.0, 0.5, 2.0, 3.5, 1.0, -0.5],
        "precipitation": 0.0,
        "snowfall": 0.0,
    })


def test_model_artifacts_load():
    assert pred.MODEL_PATH.exists() and pred.MODEL_PATH.stat().st_size > 0
    assert pred.NORM_PATH.exists() and pred.NORM_PATH.stat().st_size > 0
    assert pred.FEATURE_COLS_PATH.exists()

    import lightgbm as lgb
    booster = lgb.Booster(model_file=str(pred.MODEL_PATH))
    assert len(booster.feature_name()) > 0

    norm = pd.read_csv(pred.NORM_PATH, nrows=5)
    assert {"locationid", "day_of_week", "hour", "norm_value"} <= set(norm.columns)


def test_predict_apply_norm_compute_level_smoke():
    norm_table = pd.read_csv(pred.NORM_PATH)
    df = pred.predict(_fixture_pipeline_df())
    df = pred.apply_norm(df, norm_table)
    df = pred.compute_level(df)

    assert len(df) == 6
    assert df["predicted_deviation"].notna().all()
    assert df["predicted_busyness"].notna().all()
    assert set(df["level"].unique()) <= {"not busy", "as usual", "busier"}
