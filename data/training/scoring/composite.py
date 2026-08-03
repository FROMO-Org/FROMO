"""Presence-aware, equal-weighted composite busyness scoring, applied once
over the full stacked zone x hour panel (not invoked per month). Presence
(whether a zone structurally lacks a given mode, e.g. one of the 17
Manhattan zones with no subway station) is assessed once over the full
history, since it is a structural fact about a zone, not something that
should flip from month to month.
"""

import pandas as pd

import config
from geo import zones
from scoring import normalize


def build_zone_hour_skeleton() -> pd.DataFrame:
    """Every (kept zone, hour) combination across the full discovered date
    range - a complete, gap-free grid that every mode gets left-joined onto,
    so a zone-hour with no recorded activity becomes a genuine zero rather
    than a missing row."""
    kept_zone_ids = sorted(zones.get_kept_zone_ids())
    start, end = config.get_full_date_range()
    hours = pd.date_range(start, end, freq="h")
    return pd.MultiIndex.from_product(
        [kept_zone_ids, hours], names=[config.COL_ZONE, config.COL_HOUR]
    ).to_frame(index=False)


def build_wide_panel(mode_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Left-join each mode's (zone, hour, ride_count) output onto the full
    skeleton and zero-fill, using the same join/fill logic for every mode -
    a zone-hour with no recorded activity is handled identically regardless
    of which mode it is."""
    panel = build_zone_hour_skeleton()
    for mode, df in mode_frames.items():
        renamed = df[[config.COL_ZONE, config.COL_HOUR, config.COL_COUNT]].rename(
            columns={config.COL_COUNT: config.count_column(mode)}
        )
        panel = panel.merge(renamed, on=[config.COL_ZONE, config.COL_HOUR], how="left")
        panel[config.count_column(mode)] = panel[config.count_column(mode)].fillna(0)
    return panel


def compute_presence(panel: pd.DataFrame, modes=config.MODES) -> pd.DataFrame:
    """A mode is "present" for a zone if it has any nonzero activity for
    that zone across the full history passed in."""
    count_cols = [config.count_column(m) for m in modes]
    totals = panel.groupby(config.COL_ZONE)[count_cols].sum()
    presence = totals > 0
    presence.columns = list(modes)
    return presence


def compute_weights(presence: pd.DataFrame, modes=config.MODES) -> pd.DataFrame:
    """Presence-aware weight renormalization: a zone's weights are the
    configured base weights restricted to its present modes, rescaled to
    sum to 1 - the equal-weighted, presence-aware scheme validated in the
    legacy robustness analysis (busyness_variants_comparison_jan2025.ipynb)."""
    base = pd.Series({m: config.MODE_WEIGHTS[m] for m in modes})
    raw = presence[list(modes)].astype(float) * base
    return raw.div(raw.sum(axis=1), axis=0)


def compute_score(panel: pd.DataFrame, modes=config.MODES):
    """Fits normalization thresholds and presence-aware weights from the
    given panel (the caller passes the full-history panel so both are
    computed once, globally - see scoring/normalize.py), then returns the
    scored panel plus the fitted thresholds for persistence."""
    thresholds = normalize.fit_all(panel, modes=modes)
    panel = normalize.apply_all(panel, thresholds, modes=modes)

    presence = compute_presence(panel, modes=modes)
    weights = compute_weights(presence, modes=modes)

    score = pd.Series(0.0, index=panel.index)
    for mode in modes:
        zone_weight = panel[config.COL_ZONE].map(weights[mode]).fillna(0.0)
        score = score + zone_weight * panel[config.norm_column(mode)]
    panel["busyness_score"] = score

    # Cosmetic rescaling for display/frontend use only - not a model input -
    # reuses the identical clip-minmax method as the per-mode normalization.
    display_low, display_high = normalize.fit_threshold(panel["busyness_score"])
    panel["busyness_display"] = normalize.apply_clip_minmax(
        panel["busyness_score"], display_low, display_high
    )

    return panel, thresholds
