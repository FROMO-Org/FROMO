"""Shared point-in-polygon spatial join, used identically for both bike and
subway (point/station data) against the kept zone set resolved in
zones.py. Taxi is already zone-level and only needs that zone set for
filtering (see ingest/taxi.py), not this join.

This is also where non-Manhattan raw data actually gets removed for the
point-based modes: bike and subway are not scoped to Manhattan at ingest
time (see ingest/bike.py, ingest/subway.py docstrings), so any station
outside all kept zones - another borough, New Jersey, etc. - is dropped
here, by design, the same way for both modes.
"""

import logging

import geopandas as gpd

import config
from geo import zones
from ingest import common

logger = logging.getLogger(__name__)


def _join_points_to_zones(df) -> gpd.GeoDataFrame:
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[config.COL_LON], df[config.COL_LAT]),
        crs=config.JOIN_CRS,
    )
    kept_zones = zones.get_kept_zones()[[config.ZONE_ID_COLUMN, "geometry"]]
    joined = gpd.sjoin(points, kept_zones, how="left", predicate=config.SPATIAL_JOIN_PREDICATE)

    unmatched = joined[config.ZONE_ID_COLUMN].isna()
    if unmatched.any():
        source = df[config.COL_SOURCE].iloc[0] if len(df) else "?"
        logger.info(
            "%s: %d/%d station-hour rows fell outside all kept zones and were dropped",
            source,
            unmatched.sum(),
            len(joined),
        )
    matched = joined.loc[~unmatched].drop(columns=["geometry", "index_right"], errors="ignore")
    matched[config.ZONE_ID_COLUMN] = matched[config.ZONE_ID_COLUMN].astype(int)
    return matched


def join_points_to_zone_hours(df, source: str):
    """Join station-hour rows to the kept zone set, then aggregate to
    (zone, hour) - multiple stations commonly share a zone, so this is a
    genuine many-to-one collapse, not just a rename."""
    joined = _join_points_to_zones(df)
    result = common.aggregate_to_entity_hour(
        joined, entity_cols=[config.COL_ZONE], value_col=config.COL_COUNT
    )
    result[config.COL_SOURCE] = source
    return result
