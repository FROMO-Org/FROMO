# data

This is the ML and data-pipelines slice of the FROMO repo. It contains multiple self-contained pipelines, each living in its own subfolder with its own dependencies, tests, and CI/scheduling workflows.

## The convention

Each pipeline here follows the same shape:

- its own `requirements.txt` and `.env.example`, so its dependencies and required environment variables are documented in one place;
- its own `tests/` folder, scoped to what can be checked without secrets or a live network call;
- a **scheduled workflow** that performs the real run (with secrets, on a cron), and a separate **path-filtered CI workflow** that runs on push/PR to that subfolder and only exercises a dry-run or smoke-test path — no secrets required.

Knowing this pattern once is enough to understand any individual subfolder below.

## Root `data/` — daily busyness prediction

`predictions.py` is the daily production job. Reading the file directly: it loads the committed `model.txt` (LightGBM booster), reads `norm_table.csv` to get the list of zone ids and their per-(zone, day-of-week, hour) historical norm, builds a 24-hour calendar grid for tomorrow (NY-local date) for every zone, fetches tomorrow's hourly weather from Open-Meteo, predicts `predicted_deviation` from the model, adds it to the norm to get `predicted_busyness`, and derives a `level` label (`"not busy"` / `"as usual"` / `"busier"`) from a hybrid absolute-score/deviation rule. With `--dry-run` it logs a preview and stops there — no Supabase involved. Without it, it maps zone ids to the app's internal `area_id`s and upserts (insert-only) into the `busyness_scores` table in Supabase.

- Scheduled by `.github/workflows/daily-predictions.yml`, cron `0 9 * * *` (UTC), with `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` as secrets.
- CI'd by `.github/workflows/ci-data.yml`, triggered on pushes/PRs touching `data/**`: installs `data/requirements.txt` and runs `data/tests/` (the smoke tests below) — it does not run the real pipeline or touch Supabase.

## `data/events/` — Ticketmaster ingestion

`events/ticketmaster_ingest.py` is a separate daily job, unrelated to the busyness model. Reading the file: it fetches next-day Ticketmaster events for New York, filters them to a Manhattan polygon fetched live from NYC Open Data, upserts each event's venue into Supabase, generates a 3-sentence AI summary per event via Gemini, and upserts the events themselves into Supabase. One detail worth noting directly from the code's own docstring: Ticketmaster's Discovery API doesn't reliably expose price or capacity, so `build_price_and_capacity()` fabricates plausible values within fixed ranges for those fields rather than leaving them blank.

- Scheduled by `.github/workflows/events-ingest.yml`, cron `0 6 * * *` (UTC), with `TICKETMASTER_KEY`/`SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`/`GEMINI_API_KEY` as secrets.
- CI'd by `.github/workflows/ci-events.yml`, triggered on pushes/PRs touching `data/events/**`: runs `ticketmaster_ingest.py --dry-run` (validates config loading and the Manhattan polygon fetch, no secrets needed) plus the unit tests in `events/tests/`.

## `data/training/` — the offline model pipeline

`training/` is the offline pipeline that produced the `model.txt` / `norm_table.csv` / `feature_cols.json` that `predictions.py` consumes at runtime — see `training/README.md` for the full account. Unlike the two pipelines above, it has no workflow of its own: there is no entry for it in `.github/workflows/`, because it depends on raw data that lives outside this repository and can't run standalone in a clone. It's included for its process and reasoning to be legible, not to execute.

## The committed model artifacts

`model.txt`, `norm_table.csv`, and `feature_cols.json` live here, at the `data/` root, because `predictions.py` reads them directly at runtime. They are not duplicated anywhere else in the repo — `data/training/` is where they were produced, but doesn't keep its own copy of them.

## `zones.geojson`

A GeoJSON file of zone polygons keyed by `locationid`. `predictions.py` does not read it — it's consumed elsewhere in the app (frontend/backend rendering of zone boundaries on a map), and sits here since it's zone-id-keyed like the other artifacts.

## Secrets and configuration

Each pipeline documents its required environment variables via its own `.env.example`, with the real `.env` file gitignored everywhere in this tree:

- Root `data/.env.example`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- `data/events/.env.example`: `TICKETMASTER_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`.
