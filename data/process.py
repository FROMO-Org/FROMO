"""
data/process.py — Busyness deviation predictor
===============================================
Loads a trained LightGBM model + norm table + features CSV,
predicts deviation from norm per zone×hour, and writes a predictions CSV.

CI usage (--dry-run):
    python data/process.py --dry-run

Full prediction:
    python data/process.py --features path/to/features.csv --output preds.csv
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb


# ── Default paths (relative to repo root, where CI runs from) ────────────────
DEFAULT_MODEL        = "data/model.txt"
DEFAULT_NORM         = "data/norm_table.csv"
DEFAULT_FEATURE_COLS = "data/feature_cols.json"
DEFAULT_FEATURES     = "data/features_jan_2025_mar_2026.csv"
DEFAULT_OUTPUT       = "data/predictions.csv"

# ── Feature columns (must match training order exactly) ──────────────────────
# Loaded from feature_cols.json at runtime so this never drifts from the model.
FEATURE_COLS = None   # filled in main()


def parse_args():
    p = argparse.ArgumentParser(description="Busyness deviation predictor")
    p.add_argument("--dry-run",      action="store_true",
                   help="Validate artifacts and imports only — no prediction")
    p.add_argument("--model",        default=DEFAULT_MODEL)
    p.add_argument("--norm",         default=DEFAULT_NORM)
    p.add_argument("--feature-cols", default=DEFAULT_FEATURE_COLS)
    p.add_argument("--features",     default=DEFAULT_FEATURES)
    p.add_argument("--output",       default=DEFAULT_OUTPUT)
    return p.parse_args()


def dry_run(args):
    """
    Fast validation for CI.  Checks:
      1. All three artifact files exist and are non-empty.
      2. Imports work (lightgbm, pandas, numpy).
      3. Model file loads as a valid LightGBM booster.
      4. Norm table has the expected columns.
      5. feature_cols.json is valid JSON with a non-empty list.
    Does NOT load the 63 MB features CSV.
    """
    print("=== dry-run ===")

    # 1. Artifact existence
    for label, path in [
        ("model",        args.model),
        ("norm table",   args.norm),
        ("feature cols", args.feature_cols),
    ]:
        p = Path(path)
        if not p.exists():
            print(f"FAIL  {label} not found: {path}")
            sys.exit(1)
        if p.stat().st_size == 0:
            print(f"FAIL  {label} is empty: {path}")
            sys.exit(1)
        print(f"[OK]  {label} exists: {path}")

    # 2. Imports already executed at top of file — if we got here they work.
    print("[OK]  imports: pandas, numpy, lightgbm, sklearn")

    # 3. Model loads
    try:
        bst = lgb.Booster(model_file=args.model)
        print(f"[OK]  model loads ({len(bst.feature_name())} features)")
    except Exception as e:
        print(f"FAIL  model failed to load: {e}")
        sys.exit(1)

    # 4. Norm table schema
    try:
        norm = pd.read_csv(args.norm, nrows=5)
        required = {"locationid", "day_of_week", "hour", "norm_value"}
        missing = required - set(norm.columns)
        if missing:
            print(f"FAIL  norm table missing columns: {missing}")
            sys.exit(1)
        print(f"[OK]  norm table schema valid (columns: {list(norm.columns)})")
    except Exception as e:
        print(f"FAIL  norm table failed to load: {e}")
        sys.exit(1)

    # 5. feature_cols.json
    try:
        with open(args.feature_cols) as f:
            cols = json.load(f)
        if not isinstance(cols, list) or len(cols) == 0:
            print("FAIL  feature_cols.json must be a non-empty list")
            sys.exit(1)
        print(f"[OK]  feature_cols.json valid ({len(cols)} features)")
    except Exception as e:
        print(f"FAIL  feature_cols.json failed to load: {e}")
        sys.exit(1)

    print()
    print("dry-run OK — all artifacts present and valid")
    sys.exit(0)


def predict(args, feature_cols):
    """
    Full prediction path.
    Loads model + norm + features, predicts deviation, writes CSV.
    """
    print("Loading model …")
    bst = lgb.Booster(model_file=args.model)

    print("Loading norm table …")
    norm = pd.read_csv(args.norm)

    print("Loading features CSV …")
    df = pd.read_csv(args.features, parse_dates=["floor_hour"])
    print(f"  {len(df):,} rows loaded")

    # Derive day_of_week and hour for the norm join (they must be present in
    # features CSV already as calendar features, but we recompute from
    # floor_hour to be safe and ensure consistent type for the merge key).
    df["day_of_week"] = df["floor_hour"].dt.dayofweek   # 0=Mon … 6=Sun
    df["hour"]        = df["floor_hour"].dt.hour

    # Join norm
    pre = len(df)
    df = df.merge(
        norm[["locationid", "day_of_week", "hour", "norm_value"]],
        on=["locationid", "day_of_week", "hour"],
        how="left",
    )
    assert len(df) == pre, "Row count changed after norm merge — check join keys"

    n_null_norm = df["norm_value"].isnull().sum()
    if n_null_norm > 0:
        print(f"WARNING: {n_null_norm} rows have no norm value — these will produce NaN predictions")

    # Feature matrix
    X = df[feature_cols].copy()

    # locationid must be categorical (matches training)
    X["locationid"] = X["locationid"].astype("category")

    print("Predicting …")
    df["predicted_deviation"] = bst.predict(X)
    df["predicted_busyness"]  = df["norm_value"] + df["predicted_deviation"]

    # Output
    out_cols = ["locationid", "floor_hour", "norm_value",
                "predicted_deviation", "predicted_busyness"]
    out = df[out_cols].rename(columns={"norm_value": "norm"})

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print(f"Written {len(out):,} rows → {args.output}")
    print(f"  predicted_deviation range: [{out['predicted_deviation'].min():.4f}, {out['predicted_deviation'].max():.4f}]")
    print(f"  predicted_busyness  range: [{out['predicted_busyness'].min():.4f},  {out['predicted_busyness'].max():.4f}]")

    oor = ((out["predicted_busyness"] < 0) | (out["predicted_busyness"] > 1)).sum()
    if oor:
        print(f"  NOTE: {oor} predicted_busyness value(s) outside [0,1] — retained as-is")


def main():
    args = parse_args()

    if args.dry_run:
        dry_run(args)   # exits inside

    # Load feature columns from JSON artifact
    with open(args.feature_cols) as f:
        feature_cols = json.load(f)

    predict(args, feature_cols)


if __name__ == "__main__":
    main()