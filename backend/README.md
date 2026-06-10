# FROMO Backend

FastAPI backend for FROMO. It handles auth verification, organisation and venue management, event discovery, bookings, and saved events.

## Setup

1. Install `uv`.
2. Copy `.env.example` to `.env`.
3. Fill in:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
4. Install dependencies:

```bash
uv sync
```

5. Start the API:

```bash
uvicorn main:app --reload
```

Open Swagger docs at:

```text
http://127.0.0.1:8000/docs
```

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL via Supabase
- Supabase Auth JWT verification
- uv

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
