"""Taxi-specific raw schema handling, plugged into the shared ingest
skeleton in ingest/common.py. Mode-specific concerns, isolated here so they
cannot leak into the other modes' logic: combining the four TLC sub-datasets
(Yellow/Green/FHV/HVFHV), the passenger-count person-vs-trip duplication
(Yellow/Green only), and the Manhattan zone filter (taxi already carries a
zone id at ingest time, unlike bike/subway which are station-based and only
get a zone id later via the spatial join).

Known, deliberately preserved methodological limitation (inherited from the
legacy pipeline, not a structural bug): Yellow/Green rows are duplicated by
passenger_count so their count reflects *people*, while FHV/HVFHV have no
passenger_count field and are never duplicated, so the combined ride_count
blends person-counts with trip-counts with no adjustment for the
difference.

A sub-dataset is sometimes entirely absent for a given month (observed: FHV
is missing for Apr/May 2026, a real TLC publication gap, not a download
error) - handled as zero rows for that subtype that month, logged clearly,
rather than failing the whole month.
"""

import logging

import pandas as pd

import config
from geo import zones
from ingest import common

logger = logging.getLogger(__name__)

# Dropoff time/zone columns differ in name and casing across the four TLC
# sub-datasets; only Yellow/Green have a passenger_count field.
SUBTYPE_SPECS = {
    "yellow": {
        "glob": "yellow_tripdata_*.parquet",
        "column_map": {
            "tpep_dropoff_datetime": "datetime",
            "DOLocationID": config.COL_ZONE,
            "passenger_count": "passenger_count",
        },
        "has_passenger_count": True,
    },
    "green": {
        "glob": "green_tripdata_*.parquet",
        "column_map": {
            "lpep_dropoff_datetime": "datetime",
            "DOLocationID": config.COL_ZONE,
            "passenger_count": "passenger_count",
        },
        "has_passenger_count": True,
    },
    "fhv": {
        "glob": "fhv_tripdata_*.parquet",
        "column_map": {
            "dropOff_datetime": "datetime",
            "DOlocationID": config.COL_ZONE,
        },
        "has_passenger_count": False,
    },
    "fhvhv": {
        "glob": "fhvhv_tripdata_*.parquet",
        "column_map": {
            "dropoff_datetime": "datetime",
            "DOLocationID": config.COL_ZONE,
        },
        "has_passenger_count": False,
    },
}


def expand_by_passenger_count(df: pd.DataFrame) -> pd.DataFrame:
    """One row per person, not per trip: missing passenger_count is filled
    with 1.0 (the median/mode value), then each row is repeated that many
    times."""
    passenger_count = df["passenger_count"].fillna(1.0).astype(int)
    df = df.drop(columns="passenger_count")
    return df.loc[df.index.repeat(passenger_count)].reset_index(drop=True)


def load_subtype(month_dir, subtype: str) -> pd.DataFrame:
    spec = SUBTYPE_SPECS[subtype]
    paths = sorted(month_dir.glob(spec["glob"]))
    if not paths:
        logger.info(
            "No %s files found in %s - treating as zero rows for this "
            "subtype this month (known TLC publication gap, not an error)",
            subtype,
            month_dir,
        )
        return pd.DataFrame(columns=["datetime", config.COL_ZONE])
    raw = pd.concat(
        (pd.read_parquet(p, columns=list(spec["column_map"].keys())) for p in paths),
        ignore_index=True,
    )
    df = common.select_and_rename(raw, spec["column_map"])
    if spec["has_passenger_count"]:
        df = expand_by_passenger_count(df)
    return df


def load_raw_month(month_tag: str) -> pd.DataFrame:
    month_dir = config.RAW_TAXI_DIR / month_tag
    frames = [load_subtype(month_dir, subtype) for subtype in SUBTYPE_SPECS]
    return pd.concat(frames, ignore_index=True)


def clean_month(year: int, month: int, month_tag: str) -> pd.DataFrame:
    raw = load_raw_month(month_tag)

    kept_zone_ids = zones.get_kept_zone_ids()
    raw = raw.loc[raw[config.COL_ZONE].isin(kept_zone_ids)].copy()
    raw[config.COL_ZONE] = raw[config.COL_ZONE].astype(int)

    date_range = config.month_date_range(year, month)
    return common.clean_and_aggregate(
        raw,
        column_map={config.COL_ZONE: config.COL_ZONE, "datetime": "datetime"},
        time_col="datetime",
        entity_cols=[config.COL_ZONE],
        date_range=date_range,
        source=config.MODE_TAXI,
    )


def clean_all_months() -> pd.DataFrame:
    frames = [
        clean_month(year, month, tag) for year, month, tag in config.get_covered_months()
    ]
    return pd.concat(frames, ignore_index=True)
