"""Bike (Citibike)-specific raw schema handling, plugged into the shared
ingest skeleton in ingest/common.py. Mode-specific concern: measuring trip
ends only (arrivals), not starts — trip-start columns are never read.
"""

import pandas as pd

import config
from ingest import common

# Raw column -> common schema column. Read via usecols so the (large,
# multi-hundred-MB) raw trip files are never fully loaded into memory just to
# select four columns out of them.
RAW_COLUMN_MAP = {
    "end_station_name": config.COL_STATION,
    "ended_at": "datetime",
    "end_lat": config.COL_LAT,
    "end_lng": config.COL_LON,
}


def load_raw_month(month_tag: str) -> pd.DataFrame:
    month_dir = config.RAW_BIKE_DIR / month_tag
    csv_paths = sorted(month_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No raw bike CSVs found in {month_dir}")
    return pd.concat(
        (pd.read_csv(p, usecols=list(RAW_COLUMN_MAP.keys())) for p in csv_paths),
        ignore_index=True,
    )


def clean_month(year: int, month: int, month_tag: str) -> pd.DataFrame:
    raw = load_raw_month(month_tag)
    date_range = config.month_date_range(year, month)
    return common.clean_and_aggregate(
        raw,
        column_map=RAW_COLUMN_MAP,
        time_col="datetime",
        entity_cols=[config.COL_STATION],
        date_range=date_range,
        source=config.MODE_BIKE,
        static_cols=[config.COL_LAT, config.COL_LON],
    )


def clean_all_months() -> pd.DataFrame:
    frames = [
        clean_month(year, month, tag) for year, month, tag in config.get_covered_months()
    ]
    return pd.concat(frames, ignore_index=True)
