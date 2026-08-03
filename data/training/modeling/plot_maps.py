"""Choropleth map generation - predicted busyness and per-zone model
error, rendered onto the same 66-zone Manhattan geometry every other stage
in this pipeline resolves via geo.zones.get_kept_zones() (the single
source of truth for "which zones count" and their polygons). That
function already excludes the Governor's/Ellis/Liberty Island complex
(locationid 103/104/105) and already yields exactly one polygon per
locationid, so no separate geometry file and no dissolve step is needed
here - this module reuses it directly rather than reading a second copy
of zone geometry.

Two figures, both computed read-only against existing pipeline outputs:
  - map_predicted_busyness.png: data/processed/predictions_tomorrow.csv
    (the live one-day-ahead forecast), daily mean busyness_score per zone.
  - map_model_error.png: data/processed/test_residuals.csv, mean absolute
    error per zone on the held-out test month.

Run standalone: `python -m modeling.plot_maps`. Not wired into
run_pipeline.py - like modeling/compare.py and modeling/interpret.py, this
is a run-once, on-demand step. Writes only the two PNGs under
artifacts/figures/ (created if needed); never touches any existing
artifact or data file.
"""

import calendar
import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config
from geo import zones
from modeling import train as train_mod

FIGURES_DIR = config.ARTIFACTS_DIR / "figures"
PREDICTED_BUSYNESS_MAP_PATH = FIGURES_DIR / "map_predicted_busyness.png"
MODEL_ERROR_MAP_PATH = FIGURES_DIR / "map_model_error.png"
TEST_RESIDUALS_PATH = config.DATA_PROCESSED_DIR / "test_residuals.csv"

logger = logging.getLogger(__name__)


def _kept_zone_geometry():
    """The 66-zone geometry every stage resolves via geo/zones.py -
    already deduplicated (one polygon per locationid) and already
    excludes the island complex, so no further dissolve/exclude step is
    needed here."""
    return zones.get_kept_zones()[[config.ZONE_ID_COLUMN, "geometry"]]


def _verify_full_coverage(merged: pd.DataFrame, value_col: str, kept_zone_ids: set, context: str) -> None:
    """A silent join gap (a kept zone with no data, or a data zone outside
    the kept set) would make the map quietly wrong - fail loudly instead."""
    joined_ids = set(merged[config.ZONE_ID_COLUMN])
    if joined_ids != kept_zone_ids:
        raise ValueError(
            f"{context}: merged zone set does not match the kept 66-zone set - "
            f"extra: {sorted(joined_ids - kept_zone_ids)}, "
            f"missing entirely: {sorted(kept_zone_ids - joined_ids)}"
        )
    missing_values = merged.loc[merged[value_col].isna(), config.ZONE_ID_COLUMN].tolist()
    if missing_values:
        raise ValueError(
            f"{context}: {len(missing_values)}/{len(kept_zone_ids)} kept zones "
            f"joined but have no value (locationids: {sorted(missing_values)})"
        )
    logger.info("%s: all %d kept zones covered, zero missing values", context, len(kept_zone_ids))


def _render_choropleth(gdf, value_col, cmap, colorbar_label, title, path) -> None:
    fig, ax = plt.subplots(figsize=(8, 10))
    gdf.plot(
        column=value_col,
        cmap=cmap,
        linewidth=0.4,
        edgecolor="#777",
        legend=True,
        ax=ax,
        legend_kwds={"label": colorbar_label, "orientation": "vertical"},
    )
    ax.set_title(title)
    ax.axis("off")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_predicted_busyness() -> pd.DataFrame:
    if not config.PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"{config.PREDICTIONS_PATH} not found - run "
            "modeling.predict.predict(dry_run=False) first."
        )
    predictions = pd.read_csv(config.PREDICTIONS_PATH)
    daily_mean = predictions.groupby(config.COL_ZONE)["busyness_score"].mean().reset_index()

    zone_geom = _kept_zone_geometry()
    kept_zone_ids = set(zone_geom[config.ZONE_ID_COLUMN])
    merged = zone_geom.merge(daily_mean, on=config.ZONE_ID_COLUMN, how="left")
    _verify_full_coverage(merged, "busyness_score", kept_zone_ids, "Map 1 (predicted busyness)")

    _render_choropleth(
        merged,
        "busyness_score",
        cmap="YlOrRd",
        colorbar_label="Predicted busyness (daily mean, 0–1)",
        title="Predicted Busyness by Manhattan Zone\n(daily average, one-day-ahead forecast)",
        path=PREDICTED_BUSYNESS_MAP_PATH,
    )
    logger.info("Saved %s", PREDICTED_BUSYNESS_MAP_PATH)
    return merged[[config.ZONE_ID_COLUMN, "busyness_score"]].sort_values("busyness_score", ascending=False)


def _test_month_label() -> str:
    """Human-readable label for the held-out test month(s), derived from
    the same dynamic split train.py itself uses (config.get_covered_months()
    -> train.split_months()) rather than a typed-in literal - stays correct
    as new raw-data months are added and the test month shifts forward."""

    def _fmt(ym: int) -> str:
        year, month = divmod(ym, 100)
        return f"{calendar.month_name[month]} {year}"

    _, test_yms = train_mod.split_months()
    if len(test_yms) == 1:
        return _fmt(test_yms[0])
    return f"{_fmt(min(test_yms))} – {_fmt(max(test_yms))}"


def plot_model_error() -> pd.DataFrame:
    if not TEST_RESIDUALS_PATH.exists():
        raise FileNotFoundError(f"{TEST_RESIDUALS_PATH} not found.")
    residuals = pd.read_csv(TEST_RESIDUALS_PATH)
    mae_by_zone = residuals.groupby(config.COL_ZONE)["abs_error"].mean().rename("mae").reset_index()

    zone_geom = _kept_zone_geometry()
    kept_zone_ids = set(zone_geom[config.ZONE_ID_COLUMN])
    merged = zone_geom.merge(mae_by_zone, on=config.ZONE_ID_COLUMN, how="left")
    _verify_full_coverage(merged, "mae", kept_zone_ids, "Map 2 (model error)")

    _render_choropleth(
        merged,
        "mae",
        cmap="Purples",
        colorbar_label="Mean absolute error (test month)",
        title=f"Model Prediction Error by Manhattan Zone\n(held-out test month, {_test_month_label()})",
        path=MODEL_ERROR_MAP_PATH,
    )
    logger.info("Saved %s", MODEL_ERROR_MAP_PATH)
    return merged[[config.ZONE_ID_COLUMN, "mae"]].sort_values("mae", ascending=False)


def run_maps() -> dict:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    busyness_ranked = plot_predicted_busyness()
    error_ranked = plot_model_error()

    print("\nBusiest 5 zones (predicted, daily mean):")
    print(busyness_ranked.head(5).to_string(index=False))
    print("\nHighest-error 5 zones (test month MAE):")
    print(error_ranked.head(5).to_string(index=False))

    return {"busyness_ranked": busyness_ranked, "error_ranked": error_ranked}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    run_maps()
