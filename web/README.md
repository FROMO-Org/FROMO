# FROMO — Web App

The discovery + organiser web app for FROMO. React + Vite, Tailwind, React Router,
Leaflet (CARTO basemap tiles over OpenStreetMap data), Supabase auth, and an Axios
client against the FastAPI backend. Responsive: desktop, iOS Safari, Android Chrome.

## Run it
1. `npm install`
2. `cp .env.example .env` and fill in the values
3. `npm run dev` → http://localhost:5173

## Environment
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — Supabase project (Settings → API)
- `VITE_API_BASE_URL` — FastAPI backend (default http://localhost:8000, no global prefix)
- `VITE_ORS_API_KEY` — optional OpenRouteService key. With it, "Directions" draws an
  in-app route (wheelchair profile for step-free venues); without it, it opens Google Maps.

## Supabase auth note
For local dev, turn OFF "Confirm email" in Supabase → Authentication → Providers → Email,
so sign-up returns a session immediately and the profile row is created in one go. With it
on, the profile is created on first login instead (handled in AuthContext).

## What's wired
- Home: live feed from `GET /events/?status=active` + Leaflet/CARTO map of Manhattan.
  Accessibility badges are merged in from `GET /venues/` (the events endpoint doesn't
  return `is_accessible` yet — a one-line backend add to `event_list_item` removes the
  extra call).
- Auth: email/password via Supabase; student vs organiser written to `profiles.user_type`.

## Deferred to later sprints
- Area busyness (venues carry `busyness_area_id`; no busyness endpoint yet)
- Organiser dashboard (events/venues/orgs CRUD), saved events, bookings
- Route caching + moving the ORS key behind the backend
