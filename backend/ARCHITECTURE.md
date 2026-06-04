# FROMO — Architecture Decision Records

## Database: PostgreSQL via Supabase

### Why PostgreSQL over MySQL
PostgreSQL is the right choice for FROMO for three reasons.
First, it handles complex analytics queries better — critical for 
processing MTA and taxi datasets which have millions of rows.
Second, it has native support for UUID, numeric precision types 
(used for lat/lng and price_cents), and JSON — all used in our schema.
Third, Supabase runs on PostgreSQL, giving us a free hosted instance 
with zero configuration.

MySQL was designed for simple web apps (blogs, PHP sites). PostgreSQL 
is designed for data-heavy applications. FROMO is the latter.

### Why Supabase over a local database
A local database only exists on one machine. Every teammate would need 
to set up their own database, seed it with the same data, and keep 
schemas in sync manually. That's hours of wasted time per sprint.

Supabase gives us:
- One shared database everyone connects to instantly
- A visual dashboard to inspect and edit data without writing SQL
- Free hosted PostgreSQL with no billing risk
- Built-in authentication (Supabase Auth) that integrates directly 
  with our profiles table — we don't manage passwords ourselves
- Row Level Security (RLS) — database-level access control so the 
  mobile app can only access what it's allowed to
- Auto-generated API for simple queries — useful for rapid prototyping

The connection string in .env is the only thing that differs between 
teammates. Run `uv sync`, set your .env, start the server. Done.

### Why not use Supabase client directly (skip FastAPI)
Supabase can be queried directly from a mobile app using the 
publishable key. We chose not to do this for three reasons:

1. The busyness scoring requires Python ML inference — that computation 
   cannot live in a mobile app or in Supabase. It needs a server.
2. The secret key (full database access) must never be in a mobile app.
   FastAPI holds the secret key securely on the server.
3. Business logic (calculating total cost, generating AI summaries, 
   calling external APIs) belongs in one place — the backend. 
   Otherwise it gets duplicated across mobile and web.

FastAPI is the brain. Supabase is the memory.

---

## Schema Decisions

### Why UUID over integer for primary keys
Events will eventually be ingested from multiple sources — Eventbrite, 
NYC Open Data, venue dashboard. Integer IDs collide across sources 
(two different sources both produce id=1). UUIDs are globally unique 
regardless of source. `gen_random_uuid()` generates them automatically 
on insert.

### Why price_cents (integer) over price (float)
Floating point arithmetic is imprecise. £9.99 stored as a float can 
become £9.989999999 after arithmetic operations. Storing price as 
integer cents (999) is always exact. All price display logic divides 
by 100 in the application layer.

### Why profiles links to Supabase Auth
Supabase Auth manages user authentication — signup, login, password 
hashing, JWT tokens. Our profiles table uses the same UUID as the 
auth.users table. This means we never handle raw passwords in our 
code. Auth is a solved problem — we don't rebuild it.

### Why separate organisations and organisation_members
One organiser can own multiple venues. Multiple staff members can 
manage one organisation with different permission levels (owner, 
manager, staff). A single organisers table couldn't model this. 
The organisation_members join table with a role column handles 
both relationships cleanly.

### Why busyness_areas separate from busyness_scores
Areas are static — East Village, Midtown, etc. Scores change over 
time and are computed repeatedly. Separating them avoids repeating 
lat/lng on every score row. Venues reference busyness_area_id 
directly — the area assignment happens once at venue creation, 
not recalculated on every API request.

### Why busyness_scores has is_prediction boolean
The same table stores both raw observed data (from MTA/taxi datasets) 
and ML model predictions. is_prediction=false means historical 
observation. is_prediction=true means ML model output. The API 
queries only predictions at runtime — fast indexed lookup by 
area + day + hour. The ML pipeline writes to the same table 
with is_prediction=true. Clean separation of concerns with 
minimal complexity.

### Why indexes on (status, starts_at) for events
The most common API query is "give me active events starting soon 
near this location." Without this index, Postgres scans every event 
row. With it, it jumps directly to active events ordered by start 
time. Critical once the events table has thousands of rows.

### Why (area_id, local_day_of_week, local_hour) index on busyness_scores
The runtime busyness lookup is always "what is the score for this 
area at this hour on this day of week." The composite index makes 
this a direct lookup rather than a full table scan. With potentially 
millions of historical observations, this index is essential.

---

## Package Manager: uv over pip

uv is 10-100x faster than pip and generates a lockfile (uv.lock) 
automatically. Every teammate runs `uv sync` and gets byte-for-byte 
identical package versions. No "works on my machine" bugs from 
version mismatches across five different laptops.

pip with requirements.txt requires manual version pinning and 
doesn't guarantee reproducible environments. uv does this by default.

---

## Backend Framework: FastAPI over Flask/Django

Flask is minimal but requires significant boilerplate. Django is 
full-featured but opinionated and heavy for an API-only backend.

FastAPI is async-native — when a student opens the app, the backend 
simultaneously calls the ML model, queries the database, and calls 
external APIs (Eventbrite, routing). FastAPI handles concurrent 
requests naturally. Flask would handle them sequentially.

FastAPI also auto-generates API documentation at /docs — every 
endpoint is immediately testable by the whole team without 
writing a single line of frontend code.

---

## ORM: SQLAlchemy over raw SQL

Raw SQL for every query, insert, and update slows a team of 5 
down significantly. SQLAlchemy lets us define tables as Python 
classes and write queries in Python — readable by everyone on 
the team regardless of SQL experience.

When complex analytics queries are needed (ML data pipeline, 
busyness aggregations), we drop to raw SQL within SQLAlchemy:

    session.exec(text("SELECT ..."))

The ORM handles standard CRUD. Raw SQL handles complex analytics. 
Both coexist in the same codebase.

SQLAlchemy also makes the backend database-agnostic — switching 
from Supabase to any other PostgreSQL host requires changing 
one environment variable, nothing else.

---

## Row Level Security (RLS)

All tables have RLS enabled. By default nothing is accessible 
without an explicit policy. The FastAPI backend connects via 
the secret key which bypasses RLS — it has full access.

The mobile app will connect via the publishable key which 
respects RLS. Policies will be written in Sprint 2 when 
the mobile app begins making direct Supabase calls.

This means even if the publishable key is exposed, attackers 
can only do what the policies explicitly allow.


---


## Hosting: Supabase Free Tier

Supabase free tier provides 500MB database storage and 50,000 
monthly active users — sufficient for a student project with 
a small test dataset.

The main risk is busyness_scores table volume. Raw MTA/taxi 
datasets have millions of rows. We mitigate this by storing 
only pre-computed ML predictions in Supabase (max ~8,400 rows 
for 50 areas × 7 days × 24 hours), keeping raw datasets in 
flat files processed locally by the ML pipeline.

Note: free projects pause after 7 days of inactivity. 
A weekly keep-alive ping via GitHub Actions prevents this.

## Maps: OpenStreetMap + Leaflet + OSRM

We use OpenStreetMap instead of Google Maps for three reasons:
1. Completely free — no API key, no billing risk, no usage limits
2. Explicitly recommended in the project spec
3. Sufficient for our use case — map display, event pins, route calculation

Stack:
- Leaflet.js — map rendering in mobile and web app
- OSRM — routing and travel time calculation (walk/bike/transit)
- Nominatim — address geocoding

Google Maps was considered and rejected due to billing risk on 
a student project with no budget.