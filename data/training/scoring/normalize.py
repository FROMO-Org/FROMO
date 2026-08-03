"""Fit-once/apply clip-min-max normalization per mode. Thresholds are fit a
single time across the full available history (whatever DataFrame is passed
in - the caller, scoring/composite.py, is responsible for assembling the
complete zero-filled zone x hour panel first) rather than recomputed per
month, so busyness_score sits on one fixed scale for the whole study period.
Fitted thresholds are persisted so a later run does not silently reopen and
shift already-published values without an explicit re-fit.
"""

import json

import pandas as pd

import config


def fit_threshold(series: pd.Series) -> tuple[float, float]:
    """The [low, high] percentile bounds (config.CLIP_LOWER_PERCENTILE /
    CLIP_UPPER_PERCENTILE), computed once from the full series."""
    low = series.quantile(config.CLIP_LOWER_PERCENTILE)
    high = series.quantile(config.CLIP_UPPER_PERCENTILE)
    return float(low), float(high)


def apply_clip_minmax(series: pd.Series, low: float, high: float) -> pd.Series:
    if high <= low:
        raise ValueError(f"Invalid normalization bounds: low={low}, high={high}")
    clipped = series.clip(lower=low, upper=high)
    return (clipped - low) / (high - low)


def fit_all(df: pd.DataFrame, modes=config.MODES) -> dict[str, tuple[float, float]]:
    """Fit thresholds for every mode's raw count column in one call, using
    the same fit_threshold logic for each - no mode gets special-cased."""
    return {mode: fit_threshold(df[config.count_column(mode)]) for mode in modes}


def apply_all(
    df: pd.DataFrame,
    thresholds: dict[str, tuple[float, float]],
    modes=config.MODES,
) -> pd.DataFrame:
    df = df.copy()
    for mode in modes:
        low, high = thresholds[mode]
        df[config.norm_column(mode)] = apply_clip_minmax(
            df[config.count_column(mode)], low, high
        )
    return df


def save_thresholds(
    thresholds: dict[str, tuple[float, float]], path=config.NORMALIZATION_THRESHOLDS_PATH
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({mode: list(bounds) for mode, bounds in thresholds.items()}, f, indent=2)


def load_thresholds(path=config.NORMALIZATION_THRESHOLDS_PATH) -> dict[str, tuple[float, float]]:
    with open(path) as f:
        raw = json.load(f)
    return {mode: tuple(bounds) for mode, bounds in raw.items()}
