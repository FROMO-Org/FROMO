"""Shared clean-and-aggregate skeleton used by every transport mode: select
and rename raw columns, drop incomplete rows, filter to the target date
range, floor timestamps to the hour, and aggregate to one row per
(entity, hour). Mode-specific modules (bike.py/taxi.py/subway.py) supply only
what is genuinely mode-specific — their raw column layout, any
mode-specific row expansion (e.g. taxi's passenger-count duplication), and
which column (if any) to sum rather than count — and call
`clean_and_aggregate` for everything else, so a decision made here holds for
all three modes by construction.
"""

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def select_and_rename(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Keep only the raw columns needed downstream and rename them to the
    common schema. Selecting before dropping nulls (rather than after) means
    a null in some unrelated raw column can never cause a row to be dropped."""
    missing = [raw_col for raw_col in column_map if raw_col not in df.columns]
    if missing:
        raise KeyError(f"Expected raw columns missing from input: {missing}")
    return df[list(column_map.keys())].rename(columns=column_map)


def drop_incomplete_rows(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=subset)
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d/%d rows with nulls in %s", dropped, before, subset)
    return df


def filter_to_date_range(df: pd.DataFrame, time_col: str, start, end) -> pd.DataFrame:
    """Unconditionally applied (not just computed) so raw data outside the
    target window can never silently leak into counts, regardless of mode."""
    in_range = df[time_col].between(start, end)
    dropped = (~in_range).sum()
    if dropped:
        logger.info(
            "Dropping %d/%d rows outside [%s, %s]", dropped, len(df), start, end
        )
    return df.loc[in_range].copy()


def aggregate_to_entity_hour(
    df: pd.DataFrame,
    entity_cols: list[str],
    value_col: str | None,
    static_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Collapse to one row per (entity, hour), always via an explicit
    aggregation step. `value_col=None` means count rows (appropriate once
    row-count already reflects the desired unit, e.g. after taxi's
    passenger-count duplication); a given `value_col` means sum it instead
    (appropriate when the raw data arrives split across categories that need
    summing back down, e.g. subway's payment-method/fare-class split).
    `static_cols` (e.g. lat/lon) are carried through via first-per-entity,
    since they don't vary by hour.
    """
    group_cols = entity_cols + [config.COL_HOUR]
    if value_col is None:
        counted = df.groupby(group_cols).size()
    else:
        counted = df.groupby(group_cols)[value_col].sum()
    result = counted.rename(config.COL_COUNT).reset_index()

    if static_cols:
        statics = df.groupby(entity_cols)[static_cols].first().reset_index()
        result = result.merge(statics, on=entity_cols, how="left")

    return result


def clean_and_aggregate(
    raw_df: pd.DataFrame,
    *,
    column_map: dict,
    time_col: str,
    entity_cols: list[str],
    date_range: tuple,
    source: str,
    value_col: str | None = None,
    static_cols: list[str] | None = None,
    time_format: str | None = None,
) -> pd.DataFrame:
    """The shared skeleton, run in the same fixed order for every mode:
    select/rename -> drop incomplete rows -> parse time -> filter to date
    range -> floor to hour -> aggregate -> tag source. `time_format` is an
    optional explicit strptime format (needed for subway's raw
    "MM/DD/YYYY HH:MM:SS AM/PM" timestamps, both for correctness and because
    per-row format inference over 14M+ rows is far slower than a fixed
    format); left as None, pandas infers the format, which is fine for
    bike/taxi's ISO-like or already-parsed timestamps.
    """
    df = select_and_rename(raw_df, column_map)

    # static_cols (e.g. lat/lon) are required too: a row that can't be
    # geolocated can't be spatially joined to a zone later, so it is exactly
    # as unusable as a missing timestamp or entity id - dropped per-row here
    # rather than left to silently produce a NaN "first" value for whichever
    # (entity, hour) group it belongs to.
    required = [time_col] + entity_cols
    if value_col is not None:
        required = required + [value_col]
    if static_cols:
        required = required + static_cols
    df = drop_incomplete_rows(df, subset=required)

    df[time_col] = pd.to_datetime(df[time_col], format=time_format)
    start, end = date_range
    df = filter_to_date_range(df, time_col, start, end)

    df[config.COL_HOUR] = df[time_col].dt.floor("h")

    result = aggregate_to_entity_hour(
        df, entity_cols=entity_cols, value_col=value_col, static_cols=static_cols
    )
    result[config.COL_SOURCE] = source
    return result
