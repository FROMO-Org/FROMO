"""The single shared zone-list resolution: loads the shapefile and applies
the borough filter + exclusion rule from config to compute the kept zone
set. Every stage that needs "which zones count" (spatial join, taxi
zone-filter, feature engineering) calls this function, so the answer can
never disagree between stages.
"""

import geopandas as gpd

import config

_zones_cache: gpd.GeoDataFrame | None = None


def load_manhattan_zones() -> gpd.GeoDataFrame:
    """All Manhattan zones (before island exclusion), locationid cast to int.
    Cached at module level since every stage that needs zones reads the
    same, small shapefile."""
    global _zones_cache
    if _zones_cache is None:
        zones = gpd.read_file(config.SHAPEFILE_PATH)
        zones[config.ZONE_ID_COLUMN] = zones[config.ZONE_ID_COLUMN].astype(int)
        is_manhattan = (
            zones[config.BOROUGH_COLUMN].str.lower() == config.BOROUGH_FILTER_VALUE.lower()
        )
        _zones_cache = zones.loc[is_manhattan].reset_index(drop=True)
    return _zones_cache


def get_kept_zones() -> gpd.GeoDataFrame:
    """Manhattan zones minus the configured exclusions - the canonical
    kept-zone set used everywhere downstream. Note: in this shapefile the
    Governor's/Ellis/Liberty Island complex is stored as three polygon rows
    that all share locationid 103 (104/105 never appear as separate rows
    here) - excluding {103, 104, 105} still correctly drops all three and
    lands on the expected 66 unique zones."""
    zones = load_manhattan_zones()
    is_excluded = zones[config.ZONE_ID_COLUMN].isin(config.EXCLUDED_ZONE_IDS)
    return zones.loc[~is_excluded].reset_index(drop=True)


def get_kept_zone_ids() -> set[int]:
    return set(get_kept_zones()[config.ZONE_ID_COLUMN].tolist())
