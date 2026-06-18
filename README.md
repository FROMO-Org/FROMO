# FROMO — Web App

The discovery + organiser web app for FROMO. React + Vite, Tailwind, React Router,
Leaflet (CARTO basemap tiles over OpenStreetMap data), Supabase auth, and an Axios
client against the FastAPI backend. Responsive: desktop, iOS Safari, Android Chrome.

## Run it
1. `npm install`
2. In `.env` and fill in the values
3. `npm run dev` → http://localhost:5173

## Environment
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — Supabase project (Settings → API)
- `VITE_API_BASE_URL` — FastAPI backend (default http//localhost:8000:, no global prefix)
- `VITE_ORS_API_KEY` — optional OpenRouteService key. With it, "Directions" draws an
  in-app route (wheelchair profile for step-free venues); without it, it opens Google Maps.
