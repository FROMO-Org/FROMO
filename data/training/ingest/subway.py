"""Subway-specific raw schema handling, plugged into the shared ingest
skeleton in ingest/common.py. Mode-specific concerns, isolated here: loading
every matching raw export and deduplicating (see config.py for why a single
"newest" file cannot be trusted), restricting to actual subway rows (the raw
file also contains Staten Island Railway and Roosevelt Island Tram rows
under the same "transit_mode" column - left in by the legacy pipeline, which
mislabeled tram ridership on Roosevelt Island, a real Manhattan zone, as
subway), and summing ridership across the raw payment-method/fare-class
split down to one row per station-hour (the raw data arrives split into up
to 12 fare-class categories per station-hour; the legacy pipeline never
performed this aggregation at all).

Not scoped to Manhattan here - subway is station/point data, like bike, and
gets its zone assigned later by the spatial join in geo/spatial_join.py.
"""

import pandas as pd

import config
from ingest import common

RAW_COLUMN_MAP = {
    "transit_timestamp": "datetime",
    "station_complex": config.COL_STATION,
    "ridership": "ridership",
    "latitude": config.COL_LAT,
    "longitude": config.COL_LON,
}
TIMESTAMP_FORMAT = "%m/%d/%Y %I:%M:%S %p"
SUBWAY_TRANSIT_MODE = "subway"

# The raw data is split into up to 12 fare-class categories x 2 payment
# methods per station-hour (see module docstring). These two columns are NOT
# needed downstream, but they MUST be included when checking for duplicate
# rows across the overlapping raw files - dropping them first would make two
# genuinely different fare-class rows that happen to share the same
# ridership value look like duplicates and silently discard real ridership.
DEDUP_COLUMNS = list(RAW_COLUMN_MAP.keys()) + [
    "transit_mode",
    "payment_method",
    "fare_class_category",
]


def load_raw() -> pd.DataFrame:
    paths = config.resolve_subway_raw_paths()
    frames = [pd.read_csv(p, usecols=DEDUP_COLUMNS) for p in paths]
    raw = pd.concat(frames, ignore_index=True)

    # Values >= 1000 are comma-formatted ("1,056"), so the raw column reads
    # as string rather than numeric; must be converted before any sum/dedup,
    # or a numeric aggregation would silently concatenate strings instead of
    # adding them.
    raw["ridership"] = (
        raw["ridership"].astype(str).str.replace(",", "", regex=False).astype("int64")
    )

    before = len(raw)
    raw = raw.drop_duplicates()
    deduped = before - len(raw)
    if deduped:
        common.logger.info(
            "Dropped %d/%d exact-duplicate rows across %d subway raw files",
            deduped,
            before,
            len(paths),
        )
    raw = raw.loc[raw["transit_mode"] == SUBWAY_TRANSIT_MODE]
    return raw.drop(columns=["transit_mode", "payment_method", "fare_class_category"])


def clean_all_months() -> pd.DataFrame:
    """Subway is a single continuous file rather than one folder per month,
    so it is filtered to the pipeline's full covered date range in one pass
    instead of a clean_month/clean_all_months split like bike and taxi."""
    raw = load_raw()
    return common.clean_and_aggregate(
        raw,
        column_map=RAW_COLUMN_MAP,
        time_col="datetime",
        entity_cols=[config.COL_STATION],
        date_range=config.get_full_date_range(),
        source=config.MODE_SUBWAY,
        value_col="ridership",
        static_cols=[config.COL_LAT, config.COL_LON],
        time_format=TIMESTAMP_FORMAT,
    )
