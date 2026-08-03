"""Partial foot-traffic validation of busyness_score against NYC DOT's
public Bi-Annual Pedestrian Counts.

This is a genuinely different kind of check from validation/checks.py:
checks.py verifies internal pipeline consistency (nulls, row counts,
schema); this module compares busyness_score against an INDEPENDENT
ground-truth measurement it was never built from.

This is explicitly a PARTIAL validation, not a comprehensive one - checked
directly, not assumed:
- DOT covers 36 Manhattan locations, landing in only 22 of our 66 kept
  zones (spatially joined via geo/zones.py) - concentrated in Midtown, and
  skewed toward retail-corridor mid-block sidewalks rather than parks or
  plazas, which is exactly where the composite score is hypothesized to be
  weakest. This check cannot speak to that hypothesis directly.
- DOT's counts are not continuous: one specific weekday (7-9am, 4-7pm) plus
  the adjacent Saturday (12-2pm), twice a year (May, Sept/Oct). The exact
  day of the month is not published, so a DOT window/month is compared
  against our own AVERAGE busyness_score for that day-type and hour-range
  across the whole survey month, not one specific date.
- A recorded DOT value of 0 means "no data collected" per DOT's own readme
  (bi-annual-ped-count-readme.pdf), not a genuine zero - filtered out
  before comparison, not treated as an observation.
"""

import json
import logging

import geopandas as gpd
import pandas as pd
import requests
from scipy.stats import spearmanr

import config
from geo import zones

logger = logging.getLogger(__name__)

# (day-type, hour range, calendar month/year) for each DOT survey window
# compared. Both May 2025 and Oct 2025 fall inside this pipeline's covered
# date range (2025-01 to 2026-05) and have complete (non-zero) data for all
# 36 Manhattan locations, confirmed directly against the live dataset.
SURVEY_WINDOWS = {
    "may25_am": {"day_type": "weekday", "hours": range(7, 9), "year": 2025, "month": 5},
    "may25_pm": {"day_type": "weekday", "hours": range(16, 19), "year": 2025, "month": 5},
    "may25_md": {"day_type": "saturday", "hours": range(12, 14), "year": 2025, "month": 5},
    "oct25_am": {"day_type": "weekday", "hours": range(7, 9), "year": 2025, "month": 10},
    "oct25_pm": {"day_type": "weekday", "hours": range(16, 19), "year": 2025, "month": 10},
    "oct25_md": {"day_type": "saturday", "hours": range(12, 14), "year": 2025, "month": 10},
}


def fetch_dot_records(force_refetch: bool = False) -> list[dict]:
    if not force_refetch and config.DOT_PED_COUNTS_CACHE_PATH.exists():
        with open(config.DOT_PED_COUNTS_CACHE_PATH) as f:
            return json.load(f)

    response = requests.get(config.DOT_PED_COUNTS_URL, params={"$limit": 200}, timeout=60)
    response.raise_for_status()
    records = response.json()

    config.DOT_PED_COUNTS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.DOT_PED_COUNTS_CACHE_PATH, "w") as f:
        json.dump(records, f)
    logger.info("Fetched and cached %d DOT pedestrian-count locations", len(records))
    return records


def load_manhattan_locations_by_zone() -> pd.DataFrame:
    """DOT's Manhattan count locations, spatially joined to our kept zone
    set via the same shared geo/zones.py resolution used everywhere else in
    the pipeline."""
    records = fetch_dot_records()
    df = pd.DataFrame(records)
    manhattan = df.loc[df["borough"].str.lower() == "manhattan"].copy()
    manhattan["lon"] = manhattan["the_geom"].apply(lambda g: g["coordinates"][0])
    manhattan["lat"] = manhattan["the_geom"].apply(lambda g: g["coordinates"][1])

    points = gpd.GeoDataFrame(
        manhattan, geometry=gpd.points_from_xy(manhattan["lon"], manhattan["lat"]), crs=config.JOIN_CRS
    )
    kept = zones.get_kept_zones()[[config.ZONE_ID_COLUMN, "geometry"]]
    joined = gpd.sjoin(points, kept, how="inner", predicate=config.SPATIAL_JOIN_PREDICATE)
    return joined.drop(columns=["geometry", "index_right"], errors="ignore")


def dot_counts_by_zone(location_df: pd.DataFrame) -> pd.DataFrame:
    """One row per (window, zone): DOT's pedestrian count summed across
    every DOT location in that zone. A DOT value of 0 ("no data collected")
    is excluded before summing, not treated as a real zero."""
    rows = []
    for window in SURVEY_WINDOWS:
        counts = pd.to_numeric(location_df[window], errors="coerce").replace(0, pd.NA)
        valid = location_df.assign(_count=counts).dropna(subset=["_count"])
        by_zone = valid.groupby(config.ZONE_ID_COLUMN)["_count"].sum()
        for zone_id, total in by_zone.items():
            rows.append({"window": window, config.COL_ZONE: zone_id, "dot_count": total})
    return pd.DataFrame(rows)


def our_proxy_by_zone(scored: pd.DataFrame) -> pd.DataFrame:
    """One row per (window, zone): our own busyness_score, averaged across
    every hour in the survey month matching that window's day-type
    (weekday/Saturday) and hour range - not one specific date, since DOT
    does not publish which exact day it counted."""
    scored = scored.copy()
    scored["_hour"] = scored[config.COL_HOUR].dt.hour
    scored["_dow"] = scored[config.COL_HOUR].dt.dayofweek  # Mon=0 ... Sun=6
    scored["_year"] = scored[config.COL_HOUR].dt.year
    scored["_month"] = scored[config.COL_HOUR].dt.month

    rows = []
    for window, spec in SURVEY_WINDOWS.items():
        day_mask = scored["_dow"].eq(5) if spec["day_type"] == "saturday" else scored["_dow"].lt(5)
        mask = (
            day_mask
            & scored["_hour"].isin(spec["hours"])
            & scored["_year"].eq(spec["year"])
            & scored["_month"].eq(spec["month"])
        )
        by_zone = scored.loc[mask].groupby(config.COL_ZONE)["busyness_score"].mean()
        for zone_id, value in by_zone.items():
            rows.append({"window": window, config.COL_ZONE: zone_id, "our_busyness": value})
    return pd.DataFrame(rows)


def run_validation(scored: pd.DataFrame | None = None) -> dict:
    if scored is None:
        scored = pd.read_csv(config.BUSYNESS_SCORED_PATH, parse_dates=[config.COL_HOUR])

    location_df = load_manhattan_locations_by_zone()
    dot = dot_counts_by_zone(location_df)
    ours = our_proxy_by_zone(scored)

    merged = dot.merge(ours, on=["window", config.COL_ZONE], how="inner")

    per_window = {}
    for window in SURVEY_WINDOWS:
        subset = merged.loc[merged["window"] == window]
        if len(subset) < 3:
            per_window[window] = {"n_zones": len(subset), "spearman": None}
            continue
        corr, _ = spearmanr(subset["dot_count"], subset["our_busyness"])
        per_window[window] = {"n_zones": len(subset), "spearman": corr}

    overall_corr, _ = spearmanr(merged["dot_count"], merged["our_busyness"])

    return {
        "n_zones_covered": merged[config.COL_ZONE].nunique(),
        "n_comparisons": len(merged),
        "overall_spearman": overall_corr,
        "per_window": per_window,
        "merged": merged,
    }


def _serializable_results(results: dict) -> dict:
    """The persisted subset of run_validation()'s return value - drops
    `merged` (a DataFrame, not JSON-serializable; the per-window Spearman
    figures already summarize it). No ranked over/under-counted zone list
    is included: run_validation() doesn't compute one today (that was a
    separate, ad hoc analysis), and this entry point only persists what the
    existing validation logic already produces, per its own scope."""
    return {
        "n_zones_covered": results["n_zones_covered"],
        "n_comparisons": results["n_comparisons"],
        "overall_spearman": results["overall_spearman"],
        "per_window": results["per_window"],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")

    results = run_validation()

    output_path = config.ARTIFACTS_DIR / "paper_stats" / "foot_traffic_validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(_serializable_results(results), f, indent=2)

    print(
        f"Overall Spearman correlation: {results['overall_spearman']:.3f} "
        f"(n={results['n_comparisons']} zone-window comparisons, "
        f"{results['n_zones_covered']} zones covered)"
    )
    print("\nPer-window breakdown:")
    for window, info in results["per_window"].items():
        spearman = info["spearman"]
        spearman_str = f"{spearman:.3f}" if spearman is not None else "n/a (fewer than 3 zones)"
        print(f"  {window}: n_zones={info['n_zones']}, spearman={spearman_str}")

    print(f"\nSaved: {output_path}")
