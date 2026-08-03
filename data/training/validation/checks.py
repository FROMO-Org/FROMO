"""Shared assertion helpers (expected row count, null checks, schema/dtype
checks, uniqueness, value-range checks) called at every stage boundary in
run_pipeline.py, so every stage verifies its own output the same way
instead of each stage reinventing its own ad hoc checks.
"""

import pandas as pd


class ValidationError(AssertionError):
    pass


def assert_no_nulls(df: pd.DataFrame, columns=None, context: str = "") -> None:
    columns = columns if columns is not None else df.columns.tolist()
    nulls = df[columns].isna().sum()
    bad = nulls[nulls > 0]
    if not bad.empty:
        raise ValidationError(f"{context}: unexpected nulls -> {bad.to_dict()}")


def assert_row_count(df: pd.DataFrame, expected: int, context: str = "") -> None:
    if len(df) != expected:
        raise ValidationError(f"{context}: expected {expected} rows, got {len(df)}")


def assert_unique(df: pd.DataFrame, subset, context: str = "") -> None:
    dup_count = int(df.duplicated(subset=subset).sum())
    if dup_count:
        raise ValidationError(f"{context}: {dup_count} duplicate rows on {subset}")


def assert_columns_present(df: pd.DataFrame, required_columns, context: str = "") -> None:
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValidationError(f"{context}: missing expected columns {missing}")


def assert_value_range(
    df: pd.DataFrame, column: str, low: float, high: float, context: str = "", eps: float = 1e-9
) -> None:
    out_of_range = ~df[column].between(low - eps, high + eps)
    if out_of_range.any():
        raise ValidationError(
            f"{context}: {int(out_of_range.sum())} rows in '{column}' fall outside "
            f"[{low}, {high}] (min={df[column].min()}, max={df[column].max()})"
        )
