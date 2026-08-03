# FROMO Backend

FastAPI backend for FROMO — the single API that both the web and mobile clients run on. It handles
Supabase JWT auth verification, organisation and venue management, event discovery, bookings,
Stripe payments, AI-generated event summaries, busyness data, an organiser dashboard, and user
feedback. It also serves the busyness predictions produced offline by the data/ML pipeline.

## Setup

1. Install `uv`.
2. Copy `.env.example` to `.env`.
3. Fill in the environment variables:
   - Core (required): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`
   - Payments: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL`
   - AI summaries: `GEMINI_API_KEY`

   Feature env vars are optional — if a key is missing, that feature degrades gracefully (e.g. an
   event is still created without an AI summary).
4. Install dependencies:

```bash
uv sync
```

5. Start the API:

```bash
uv run uvicorn main:app --reload
```

Open Swagger docs at:

```text
http://127.0.0.1:8000/docs
```

## Stack

- FastAPI (typed REST API, auto-generated OpenAPI docs)
- SQLAlchemy (ORM)
- PostgreSQL via Supabase
- Supabase Auth JWT verification (JWKS)
- Stripe (hosted Checkout + webhook)
- Gemini API (event summaries)
- uv (package manager)
- pytest + GitHub Actions CI

## Current API Flow

Typical organiser flow:

1. `POST /profiles/me`
2. `POST /organisations/`
3. `POST /venues/`
4. `POST /events/`
5. `PATCH /events/{event_id}` to publish/update status

Typical student flow:

1. `POST /profiles/me`
2. `GET /events/`
3. `GET /venues/{venue_id}`
4. `POST /saved-events/`
5. `POST /bookings/`
6. `GET /bookings/me`
7. `GET /saved-events/me`

## Main Endpoints

Profiles:
- `POST /profiles/me`
- `GET /profiles/me`
- `PATCH /profiles/me`

Organisations:
- `POST /organisations/`
- `GET /organisations/me`
- `GET /organisations/{organisation_id}`
- `GET /organisations/{organisation_id}/events`
- `POST /organisations/{organisation_id}/members`

Venues:
- `POST /venues/`
- `GET /venues/`
- `GET /venues/{venue_id}`

Events:
- `GET /events/`
- `GET /events/{event_id}`
- `POST /events/`
- `PATCH /events/{event_id}`
- `DELETE /events/{event_id}`

Bookings:
- `GET /bookings/me`
- `POST /bookings/`
- `PATCH /bookings/{booking_id}`

Saved events:
- `GET /saved-events/me`
- `POST /saved-events/`
- `DELETE /saved-events/{event_id}`

Payments (Stripe):
- `POST /payments/` — start a Checkout session for an event
- `GET /payments/{payment_id}` — payment status
- `POST /payments/webhook` — Stripe webhook (confirms the booking on `checkout.session.completed`)

Busyness:
- `GET /busyness/areas` — list static busyness zones
- `GET /busyness/areas/{area_id}/scores` — scores for a zone
- `GET /busyness/nearby` — zones and scores near a coordinate

Dashboard:
- `GET /organisations/{organisation_id}/dashboard` — organiser analytics (listings, bookings, revenue)

Feedback:
- `POST /feedback/`

## Notes For Frontend/Data ML

- Authenticated endpoints require a Supabase JWT in the `Authorization: Bearer <token>` header.
- `GET /events/` always returns items shaped as `{ event, distance_km, venue }`.
- `distance_km` is `null` unless `lat` and `lng` are provided.
- `GET /bookings/me` returns `{ booking, event, venue }`.
- `GET /saved-events/me` returns `{ saved_event, event, venue }`.
- UUID fields are validated by FastAPI before hitting PostgreSQL.
- Supabase has database constraints for statuses, non-empty names, coordinates, prices, quantities, and event time ordering.

## Sanity Checks

```bash
.venv/bin/python -m compileall app main.py
.venv/bin/python -B -c "from main import app; print(len(app.routes))"
```

## Testing

The suite (~99 tests, ~60% statement coverage across `app/`) covers schema/validation, API
behaviour, OpenAPI contract registration, dashboard logic, and the Stripe webhook flow (including
idempotency). Tests use mocked authentication and, in CI, run against a real PostgreSQL container.

```bash
uv run pytest                                  # run the suite
uv run --with pytest-cov pytest --cov=app      # with coverage
uv run ruff check .                            # lint
```

## Continuous Integration

`.github/workflows/ci-backend.yml` runs on every push/PR touching `backend/`. It checks the `uv`
lockfile is in sync, runs `ruff`, spins up a PostgreSQL 17 service container, and runs `pytest` —
so regressions are caught before they merge.

## Performance

A dependency-free load-test harness reports p50/p95/p99 latency per endpoint:

```bash
python3 perf/load_test.py <BASE_URL> --requests 40 --concurrency 1     # per-request cost
python3 perf/load_test.py <BASE_URL> --requests 150 --concurrency 20   # under load
```

## Supabase Workflow

### What changed

We now keep database schema changes in `backend/supabase/migrations/` instead of relying only on
manual edits in the Supabase dashboard.

### What teammates need

- Supabase CLI installed
- Docker Desktop running when using Supabase database tools like `db pull`, `db diff`, or local
  Supabase services

### One-time setup

Run these from `backend/`:

```bash
supabase login
supabase link
```

### Normal coding

Most of the time, teammates do not need to run Supabase commands.

Normal feature work is usually just:

```bash
git pull
uv sync
uv run uvicorn main:app --reload
```

Use the shared online Supabase database as usual.

### When changing the database schema

If you need to add a table, column, constraint, or index:

1. Create a feature branch
2. Create a migration file
3. Edit the SQL in VS Code
4. Commit the migration file
5. After review, apply it to the shared remote database

Example:

```bash
git checkout -b feat/payments
cd backend
supabase migration new add_payments
```

That creates a SQL file in:

```text
backend/supabase/migrations/
```

After editing the SQL file, apply it to the linked remote Supabase project:

```bash
supabase db push
```

### Useful Supabase commands

Run these from `backend/`:

```bash
supabase migration list
supabase migration new add_something
supabase db push
```

### Dashboard rule

The Supabase dashboard is still fine for:

- viewing tables
- checking rows
- inspecting auth users
- inspecting logs

Try not to make schema changes directly in the dashboard first. Prefer migration files so the
database structure stays tracked in Git.

## Render Deploy Settings

### Backend service

Render service type:

- Web Service

Root directory:

```text
backend
```

Build command:

```bash
uv sync
```

Start command:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

Backend environment variables to set in Render:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- `FRONTEND_URL` (used for Stripe redirect URLs — set to the deployed frontend origin)
- `GEMINI_API_KEY`

### Frontend site

Render service type:

- Static Site

Root directory:

```text
web
```

Build command:

```bash
npm install && npm run build
```

Publish directory:

```text
dist
```

There is no start command for a Render Static Site.

Frontend environment variables to set in Render:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL`
- optional: `VITE_ORS_API_KEY`
