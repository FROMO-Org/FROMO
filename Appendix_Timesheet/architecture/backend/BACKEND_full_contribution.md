# FROMO — Backend contribution (Danila) — full write-up for the paper

Everything I did on the backend, organised so it drops into the paper's sections.
Maps to: **Methodology** (architecture, dev process, testing, CI), **Evaluation & Results**
(testing + performance), and the **contributions** summary.

Note for whoever assembles: the two performance tables need `\usepackage{booktabs}` in the
preamble. All numbers here are real and reproducible with `backend/perf/load_test.py`.

---

## 1. Role & overview

I was the **backend lead**. I built the server layer that both the web and mobile clients run
on: a **FastAPI** application with **SQLAlchemy** over a **PostgreSQL** database hosted on
**Supabase**, deployed on Render. This is the integration point the whole team builds against —
the two front-ends and the ML pipeline all connect through my API and database.

## 2. Architecture & technology choices

- **FastAPI (Python)** over Django (too heavy/opinionated for this) and Node/Express (would have
  split the API from our Python ML work). FastAPI gives typed request/response validation and an
  auto-generated OpenAPI schema, which I assert in tests.
- **SQLAlchemy ORM** over raw SQL: one schema definition in Python, safer queries, portability.
- **Supabase** for managed PostgreSQL + authentication, and **Stripe** for payments — deliberately
  *not* rolling my own auth or card handling, so sensitive data stays with specialists.
- **uv** as the package manager: Rust-based, fast, reproducible from a lockfile.
- **All business logic server-side** so the two clients cannot diverge (single source of truth).

## 3. API design

A **10-router REST API**, grouped by concern:
- Identity: `profiles`, `organisations`
- Content: `events`, `venues`
- Engagement: `bookings`, `saved_events`, `feedback`
- Commerce: `payments`
- Insight: `busyness`, `dashboard`

Clients send HTTP requests (GET/POST/PATCH) and receive JSON. Input validation (e.g. price cannot
be negative) lives in a schema layer so invalid requests are rejected before hitting the database.

## 4. Database schema

An **11-table relational schema** I designed:
- People/orgs: `profiles`, `organisations`, `organisation_members` (with a role)
- Places/events: `venues`, `events`
- Busyness: `busyness_areas` (static zones) and `busyness_scores` (time-varying) — a deliberate
  split so repeated zone geometry isn't duplicated against every hourly score, with an
  `is_prediction` flag so model predictions are never shown as measurements
- User actions: `saved_events`, `bookings`, `feedback`, `payments`

Chose PostgreSQL (relational) over a document store because the data is highly relational
(foreign keys, joins) and, critically, a booking/payment system needs **transactions (ACID)** —
a booking, its payment, and the capacity change must be all-or-nothing.

## 5. Authentication

Supabase issues a signed **JWT** on login. On each request the backend verifies the token's
**signature against Supabase's public keys (JWKS)**, checking the `ES256`/`RS256` signature and the
`authenticated` audience. This is **stateless** — no session table — and **no password is ever
stored by us**. Organisation-scoped routes additionally check the caller's membership role.

## 6. Payments

**Stripe hosted Checkout** takes the card, so card data never touches our servers (keeps us out of
PCI scope). The booking is confirmed **only** on a **signed webhook** from Stripe
(`checkout.session.completed`), verified with the webhook secret — not on the browser redirect,
which could be faked or never arrive. The handler is **idempotent** (it checks the payment's state
first), so Stripe re-delivering the webhook cannot create a second booking. Payment states:
`pending -> paid / expired / failed`.

## 7. AI summary feature

On event creation the backend calls the **Gemini API** to generate a short summary of the event
from its details, so organisers don't have to write listing copy. It fails gracefully — if the call
fails the event is still created, just without a summary — and I hardened it with a timeout, a
retry on transient errors, and logging so production failures are diagnosable.

## 8. Testing (full explanation)

The backend has a suite of **~99 automated tests**, organised by concern, giving **~60% statement
coverage** across `app/`. The suite mixes several kinds of test:

- **Schema / validation tests** confirm request bodies validate correctly — e.g. an event price
  must be a non-negative number, not letters.
- **Contract tests** assert that every core route is registered in the auto-generated **OpenAPI
  schema** with the correct path-parameter types. This means an accidental change to an endpoint's
  signature fails CI *before* it can break the web or mobile clients.
- **API / behaviour tests** exercise the endpoints end to end — event CRUD, booking create and
  cancel, the payment checkout and webhook flow, dashboard calculations.
- **A webhook idempotency test** verifies that a re-delivered Stripe webhook does not create a
  second booking — the highest-risk path in the system.

Tests use **mocked authentication**, so they don't depend on the live Supabase instance, and in CI
they run against a **real PostgreSQL 17 container** (not SQLite or mocks), so Postgres-specific
behaviour — UUID defaults, a partial unique index — is genuinely exercised. Coverage is uneven and
worth stating honestly: the `saved_events`, `profiles`, `feedback`, and `busyness` routers have no
dedicated tests and are exercised only indirectly through contract assertions.

## 9. Continuous Integration

A **GitHub Actions** workflow runs on every push/PR that touches the backend. It: checks the **uv
lockfile** is in sync (reproducible dependencies), runs **ruff** (lint), spins up a **PostgreSQL 17**
service container, and runs **pytest**. The value is an **automatic safety net** — a change that
breaks an endpoint or the schema is caught before it merges, so broken code never reaches
production, and every contributor's work is verified the same way.

## 10. Performance evaluation

Backend latency was measured against the deployed instance with a lightweight, dependency-free
harness (`backend/perf/load_test.py`) reporting response-time percentiles per endpoint. Five
endpoints were chosen to isolate different cost sources. Each was tested by a single client
(intrinsic cost) and then by twenty concurrent clients (behaviour under load).

**Table 1 — single client (ms):**

| Endpoint | p50 | p95 | p99 |
|---|---|---|---|
| /health (baseline) | 66 | 127 | 185 |
| /events (list) | 118 | 136 | 144 |
| /events/{id} (indexed) | 96 | 108 | 113 |
| /busyness/areas (list) | 106 | 177 | 260 |
| **/busyness/nearby (spatial)** | **757** | **836** | **885** |

**Table 2 — 20 concurrent clients (ms, + req/s):**

| Endpoint | p50 | p95 | p99 | req/s |
|---|---|---|---|---|
| /health | 111 | 176 | 192 | 158 |
| /events | 742 | 1570 | 1673 | 24 |
| /events/{id} | 497 | 897 | 1094 | 36 |
| /busyness/areas | 810 | 1253 | 1457 | 22 |
| **/busyness/nearby** | **4690** | **7635** | **7930** | **4** |

Most endpoints respond in ~100–180 ms at p95 under a single client; the indexed `/events/{id}`
lookup is the fastest DB-backed route. The clear outlier is **`/busyness/nearby`**, ~6–8× slower
even unloaded and collapsing to ~4.7 s under concurrency. The cause is an **N+1 query pattern**: it
loads *every* busyness area, then issues a *separate* query per area for its latest score — roughly
**68 database round-trips** for one request (with 67 areas). The fix, identified as the principal
performance limitation, is to push a bounding-box predicate into SQL and collapse the per-area
lookups into a single `DISTINCT ON` query, reducing ~68 round-trips to two.

(The IEEE LaTeX for both tables is in `group_essay_v1.tex`; ask me if you need it separately.)

## 11. Honest limitations (self-critical — worth including)

- Busyness is a **batch prediction** read from the database, not a live feed.
- Schema changes use **additive DDL at startup**, not full migrations — fine for a prototype,
  but a production system would need a managed migration tool.
- **Test coverage is ~60%** and uneven — four routers lack dedicated tests.
- The **N+1** in `/busyness/nearby` is identified but not yet optimised.

---

## Where this maps in the paper
- **Methodology → Architecture:** sections 2–7.
- **Methodology → Development process/CI:** sections 8–9.
- **Evaluation & Results → System/code testing:** section 8.
- **Evaluation & Results → Performance:** section 10 (+ the two tables).
- **Conclusion → Limitations/Future work:** section 11.
