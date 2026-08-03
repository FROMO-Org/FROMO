"""Regression check: diff the new pipeline's real output against the
legacy pipeline's trusted Jan 2025 output. Requires run_pipeline.py to have
been run at least once (reads data/processed/busyness_scored.csv from disk;
does not regenerate it here, since a full run takes several minutes).

Exact numeric equality is NOT the goal, by design:
- The new pipeline fits normalization thresholds globally across the full
  history (scoring/normalize.py), while legacy refit them independently
  every month - a deliberate fix for legacy's per-month scale drift
  (DATA_ML_HANDOFF.md limitation #7), not a bug. This alone means
  busyness_score will differ somewhat even for a month where the raw
  counts match exactly.
- Small, disclosed differences in raw mode counts are also expected: the
  tram/Staten-Island-Railway exclusion fix in ingest/subway.py (~0.3% of
  Jan-2025 subway ridership), and stricter null-handling in
  ingest/common.py (a small fraction of a percent for bike). Both were
  independently verified against raw data during development - see project
  memory for the exact figures.

What this test actually checks:
  - every zone-hour in the comparison month is present on both sides (no
    silent coverage gap)
  - raw mode counts (subway/taxi/bike) agree with legacy within a loose
    tolerance that comfortably covers the known, disclosed fixes above
  - busyness_score rank-correlates strongly with legacy's, using Spearman
    correlation - the same method legacy's own robustness analysis used to
    compare its four candidate scoring variants against each other
  - the mean absolute difference in busyness_score is bounded, as a
    backstop against a gross, unexplained divergence
"""

import pandas as pd
import pytest
from scipy.stats import spearmanr

import config

JAN_2025_START = pd.Timestamp("2025-01-01 00:00:00")
JAN_2025_END = pd.Timestamp("2025-01-31 23:00:00")
EXPECTED_ROWS = 66 * 744

# Loose but meaningful bounds - see module docstring for why exact equality
# isn't the goal.
MAX_RELATIVE_COUNT_DIFF = 0.02
MIN_SPEARMAN_CORRELATION = 0.9
MAX_MEAN_ABS_SCORE_DIFF = 0.05

LEGACY_JAN_2025_PATH = config.LEGACY_DIR / "shapefile" / "busyness_jan_2025.csv"


@pytest.fixture(scope="module")
def merged() -> pd.DataFrame:
    if not config.BUSYNESS_SCORED_PATH.exists():
        pytest.skip(
            f"{config.BUSYNESS_SCORED_PATH} does not exist yet - run "
            f"run_pipeline.py first to produce it."
        )
    if not LEGACY_JAN_2025_PATH.exists():
        pytest.skip(f"legacy comparison file not found: {LEGACY_JAN_2025_PATH}")

    new = pd.read_csv(config.BUSYNESS_SCORED_PATH, parse_dates=[config.COL_HOUR])
    new = new.loc[new[config.COL_HOUR].between(JAN_2025_START, JAN_2025_END)]

    legacy = pd.read_csv(LEGACY_JAN_2025_PATH, parse_dates=[config.COL_HOUR])

    return new.merge(
        legacy,
        on=[config.COL_ZONE, config.COL_HOUR],
        suffixes=("_new", "_legacy"),
        how="outer",
        indicator=True,
    )


def test_row_coverage_matches_legacy(merged):
    assert len(merged) == EXPECTED_ROWS, (
        f"expected {EXPECTED_ROWS} zone-hours (66 zones x 744 hours), got {len(merged)}"
    )
    mismatched = merged.loc[merged["_merge"] != "both"]
    assert mismatched.empty, (
        f"{len(mismatched)} zone-hours present on only one side (new-only or "
        f"legacy-only), expected full overlap for the same 66-zone canonical set"
    )


@pytest.mark.parametrize("mode", ["subway", "taxi", "bike"])
def test_raw_mode_counts_match_legacy_closely(merged, mode):
    new_total = merged[f"{mode}_count_new"].sum()
    legacy_total = merged[f"{mode}_count_legacy"].sum()
    relative_diff = abs(new_total - legacy_total) / legacy_total
    assert relative_diff < MAX_RELATIVE_COUNT_DIFF, (
        f"{mode}_count total differs from legacy by {relative_diff:.2%} "
        f"(new={new_total}, legacy={legacy_total}), exceeding the "
        f"{MAX_RELATIVE_COUNT_DIFF:.0%} tolerance meant to comfortably cover "
        f"known/disclosed fixes (tram exclusion, stricter null-handling)"
    )


def test_busyness_score_rank_correlates_with_legacy(merged):
    correlation, _ = spearmanr(merged["busyness_score_new"], merged["busyness_score_legacy"])
    assert correlation > MIN_SPEARMAN_CORRELATION, (
        f"Spearman correlation with legacy busyness_score is only "
        f"{correlation:.4f}, expected > {MIN_SPEARMAN_CORRELATION}"
    )


def test_busyness_score_mean_diff_bounded(merged):
    mean_abs_diff = (merged["busyness_score_new"] - merged["busyness_score_legacy"]).abs().mean()
    assert mean_abs_diff < MAX_MEAN_ABS_SCORE_DIFF, (
        f"mean abs diff in busyness_score is {mean_abs_diff:.4f}, expected "
        f"< {MAX_MEAN_ABS_SCORE_DIFF} (global-vs-per-month normalization is "
        f"expected to shift values somewhat, but not this much)"
    )
