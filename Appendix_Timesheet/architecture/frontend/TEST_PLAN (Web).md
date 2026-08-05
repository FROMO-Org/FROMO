# Web Test Plan

This document outlines the testing strategy for the React web app (student discovery + partner dashboard).

## Goals

- Catch regressions in app logic and UI behaviour early
- Protect critical user flows such as login, event discovery, saved events, and venue/listing management
- Reduce reliance on a live backend and Supabase session during development
- Keep the service/data layer (`lib/`) independently testable from the UI

## Test Categories

### 1. Unit Tests

Focus on pure logic — formatting, parsing, and request-building — with no rendering involved.

Recommended coverage:

- `format.js` — currency, time, and distance formatting
- `directions.js` — geocoding and route-fetch request shaping, ORS error handling
- `api.js` — discover-feed pagination (`hasMore` calculation), venue enrichment/join logic

Why this matters:

- Fastest and cheapest tests to run and maintain
- Best place to lock down business rules that don't depend on the DOM

### 2. Component Tests

Use React Testing Library to render components/pages in isolation, mocking context and router dependencies.

Recommended coverage:

- `EventCard` — renders event/venue data, accessibility badges, price formatting, click-to-navigate and Directions-button behaviour for both signed-in and signed-out users
- `Header` — nav/auth-state rendering for logged-out, student, and organiser sessions
- `Login` — form submission, role-based redirect (`/` vs `/partner`) driven by the account's actual `profile.user_type`, error and busy states
- `AuthContext` — session/profile loading, sign-up/sign-in/sign-out behaviour against a mocked Supabase client

Why this matters:

- Catches UI and behavioural regressions without a live backend or auth session
- Keeps tests deterministic by mocking `AuthContext` and `useNavigate` rather than relying on real routing/auth side effects

### 3. Integration Tests

Not yet implemented. Would exercise multiple components/pages together through real React Router navigation (still against a mocked API layer).

Candidate coverage:

- sign-in redirects into the correct feed/dashboard and back-navigation behaves correctly
- discover feed filter + pagination + map-selection interaction working together
- partner venue creation → listing creation → listing appears in the dashboard

### 4. End-to-End Tests

Not yet implemented (no Playwright/Cypress in the project). Would run against the deployed or a local build with a real backend.

Candidate coverage:

- student signs up, browses the feed, saves an event, and books it
- partner signs up, creates a venue and listing, and sees it appear on the student feed
- paid booking flow through Stripe checkout and the `CheckoutRedirect` return page

Why this matters:

- Highest realism, highest maintenance cost — should stay limited to a handful of critical journeys if added

### 5. Visual and Responsive Tests

Not yet implemented. The app is manually verified across desktop, iOS Safari, and Android Chrome per the project README, but there is no automated visual regression coverage.

Candidate coverage:

- discover feed (map + list) at mobile, tablet, and desktop widths
- partner dashboard layout at narrow widths
- dark mode vs light mode for key screens

### 6. API Mocking

All current component/page tests mock their dependencies rather than hitting a live backend or Supabase:

- `AuthContext`'s `useAuth` is mocked via `vi.mock` in component/page tests, returning controlled `user`/`profile`/`signIn`/`signOut` values per test case
- `react-router-dom`'s `useNavigate` is mocked to assert on navigation calls without a real router transition
- `AuthContext.test.jsx` itself mocks the underlying Supabase client so auth logic can be tested without network calls

Why this matters:

- Lets the suite run fully offline and deterministically in CI
- Makes edge cases (e.g. signed-out click behaviour, failed sign-in) easy to set up directly

## Recommended Priority

### Phase 1 — Status: implemented

- Unit tests (`lib/`)
- Component/page tests (`components/`, `pages/`, `context/`)
- API mocking via `vi.mock`

### Phase 2 — Status: not yet implemented

- Integration tests across full page flows with real router navigation

### Phase 3 — Status: not yet implemented

- Visual/responsive regression tests
- A small number of end-to-end tests against the deployed app

## Implemented Baseline

Phase 1 currently includes:

- `src/lib/__tests__/format.test.js`
- `src/lib/__tests__/directions.test.js`
- `src/lib/__tests__/api.test.js`
- `src/components/__tests__/EventCard.test.jsx`
- `src/components/__tests__/Header.test.jsx`
- `src/pages/__tests__/Login.test.jsx`
- `src/context/__tests__/AuthContext.test.jsx`

7 test files, 60 tests, run via `npm test` (`vitest run`) and enforced in CI (`.github/workflows/ci-web.yml`) on every push/PR touching `web/**`, alongside a production `npm run build` check.

## Suggested File Structure

```text
web/
├── src/
│   ├── components/__tests__/
│   ├── pages/__tests__/
│   ├── context/__tests__/
│   ├── lib/__tests__/
│   └── setupTests.js
└── TEST_PLAN.md
```

## Implementation Notes

- Prefer mocking `AuthContext` and router hooks over rendering with a real `AuthProvider`/live Supabase session
- Keep `lib/` tests focused on request shaping and pure logic, not rendering
- Keep component tests focused on what the user sees and does, not implementation details
- When product behaviour changes intentionally (e.g. login's role-tab removal in favour of profile-driven redirect), update the test to match the new behaviour rather than reverting the product change — confirm with the person who owns that surface before assuming which way a mismatch should be resolved

## Definition of Done

The web testing baseline is considered in place when:

- the service/data layer (`lib/`) has unit coverage for its non-trivial logic (pagination, geocoding, formatting)
- primary auth flows (login, session-driven redirect) have component coverage
- core shared components (`EventCard`, `Header`) have coverage for both signed-in and signed-out states
- the full suite runs in CI on every push/PR without requiring a live backend or Supabase project
