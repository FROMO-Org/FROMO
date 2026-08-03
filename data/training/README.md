# data/training

This is the offline pipeline that produced the deployed model artifacts sitting in the parent `data/` folder (`model.txt`, `norm_table.csv`, `feature_cols.json`). It's committed so the training process is legible and auditable, not because it's meant to run — it isn't wired into CI, and it isn't expected to execute in a clone. Raw data is excluded from the repo for size and lives outside it, so this folder is here to be read, not executed.

## What the pipeline does

The model predicts how far a given zone-hour's `busyness_score` deviates from that zone-hour's own historical norm (e.g. "Tuesdays at 6pm in this zone"), rather than predicting busyness directly. It's built from three NYC transport datasets — subway ridership, taxi trips, Citibike trips — combined into a composite busyness score per Manhattan zone per hour, plus hourly weather and calendar features (holiday, day of week, month).

## Stage order

`run_pipeline.py` is the entry point and runs the stages below in order in a single process:

1. **`ingest/`** (`bike.py`, `taxi.py`, `subway.py`, `common.py`) — cleans each mode's raw data to a common (entity, hour) schema. Bike and subway are station-level and get their zone assigned via a spatial join (`geo/spatial_join.py`) against the zone set resolved in `geo/zones.py`; taxi already carries a zone id.
2. **`scoring/`** (`composite.py`, `normalize.py`) — assembles the full zero-filled zone × hour panel, fits per-mode normalization, and combines the three modes into one presence-aware composite `busyness_score`.
3. **`features/build_features.py`** — joins on calendar features and historical weather (`weather/historical.py`), producing the model-ready features table.
4. **`modeling/train.py`** — computes the expanding-window historical norm, trains the LightGBM deviation model, and exports the model, norm table, feature list, and level thresholds to `artifacts/`.

`validation/checks.py`'s assertions (null checks, row counts, uniqueness, value ranges) run inline at every stage boundary above, rather than as a separate final step. `validation/foot_traffic.py` is a separate, standalone check — comparing `busyness_score` against NYC DOT's public pedestrian counts — and is not called by `run_pipeline.py`.

A few modules are standalone, run-once steps, also not wired into `run_pipeline.py`: `modeling/compare.py` (alternative-model comparison), `modeling/interpret.py` (feature importance + SHAP), `modeling/plot_maps.py` (choropleth figures), and everything under `analysis/`.

## What's committed vs. excluded

- **Source code**: every stage package above (`ingest/`, `geo/`, `scoring/`, `features/`, `modeling/`, `validation/`, `weather/`), `config.py` (single source of truth for paths, date ranges, zone rules, model hyperparameters), and `tests/test_regression_vs_legacy.py`.
- **Generated artifacts** (committed so results are inspectable without re-running anything): `artifacts/feature_importance.csv`, `artifacts/model_comparison.csv` / `.json`, `artifacts/level_thresholds.json`, `artifacts/normalization_thresholds.json`, `artifacts/figures/*.png` (feature importance, SHAP summary/bar, predicted-busyness and model-error maps), and `artifacts/paper_stats/*` (per-zone/hour/day-of-week/holiday error breakdowns, SHAP importance, dataset manifest, foot-traffic validation). Note: `model.txt`, `norm_table.csv`, and `feature_cols.json` are **not** duplicated here — this pipeline is what produces those files, and the versions actually in use live only in the parent `data/`.
- **Excluded**: raw per-mode data and large processed CSVs, per `../.gitignore` (`*.parquet`, `*.csv.gz`, and the large intermediate feature/prediction CSVs by name).

## The external-data dependency

`config.py` resolves raw data relative to a `Busyness/` folder that sits outside this repo. That means ingestion can't run standalone in a clone — this is a deliberate boundary (raw data excluded for size), not a bug.

## Analysis and experiments

`analysis/` holds read-only diagnostics against the trained model and features: `model_errors.py` (error breakdowns by zone/hour/day-of-week/holiday/weather), `event_signal_check.py` (whether MSG event hours carry signal beyond the current feature set), and `export_paper_stats.py` (persists those numbers to `artifacts/paper_stats/`).

`analysis/experiments/` holds a rejected experiment, kept deliberately rather than deleted: `trend_feature_test.py` tests adding a `months_since_start` feature on a single held-out month, and `trend_feature_walkforward.py` re-checks it across multiple months. `months_since_start` is not in `config.FEATURE_COLUMNS` in the final pipeline — these files are the record of that idea being tried and not kept, not an in-progress feature.

## No credentials

This pipeline touches no database and holds no credentials — there is no `.env` file, connection string, or API key anywhere in this folder. The only network call in the whole pipeline is a read-only fetch to the public Open-Meteo weather API.
