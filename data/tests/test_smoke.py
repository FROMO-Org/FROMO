"""
End-to-end smoke test for process.py's prediction path.

Runs the real CLI against a small, committed fixture (6 rows, single
locationid covered by norm_table.csv) and checks the output is well-formed.
This is not an accuracy test — it just confirms the norm join, feature
ordering, and model call still work end-to-end without needing the large
(gitignored) production features CSV.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_features.csv"


def test_predict_smoke(tmp_path):
    output = tmp_path / "predictions.csv"

    result = subprocess.run(
        [
            sys.executable, str(DATA_DIR / "process.py"),
            "--features", str(FIXTURE),
            "--output", str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    fixture_rows = len(pd.read_csv(FIXTURE))
    out = pd.read_csv(output)

    assert len(out) == fixture_rows
    assert list(out.columns) == [
        "locationid", "floor_hour", "norm",
        "predicted_deviation", "predicted_busyness",
    ]
    assert out["predicted_deviation"].notna().all()
    assert out["predicted_busyness"].notna().all()
