# FROMO
FROMO (Free from FOMO) is a real-time, location-based event discovery platform designed to help students find meaningful things to do nearby, especially last-minute and low-friction social activities. Instead of relying on endless scrolling or fragmented event listings, FROMO brings nearby events, venue context, booking tools, and local busyness signals into one map-first experience.

The project responds to a common student problem: people often want to go out, meet others, or try something spontaneous, but they miss opportunities because information is scattered, outdated, or not location-aware. FROMO reduces that friction by showing what is happening around the user right now, supporting quick decisions through distance, category, price, time, availability, directions, and reservation status.

FROMO also supports event organisers and venues. Partners can create and manage event listings, monitor bookings and revenue, and use analytics to understand engagement. The backend is built around Supabase, FastAPI, and PostgreSQL, with room for data-driven demand and busyness modelling using NYC neighbourhood-level spatial data.

---

## Features

### Student Experience

- Map-based discovery of live and upcoming events
- Nearby mode using the user's location and a radius-based event feed
- All-events mode for browsing the wider Manhattan event dataset
- Event cards with title, category, time, distance, price, venue, and availability
- Category filtering for faster discovery
- Event detail pages with images, descriptions, venue information, dates, times, prices, remaining spots, and directions
- Save and unsave events for later
- Book free events directly through the app
- View upcoming, past, and cancelled bookings
- Cancel confirmed bookings before the event
- Direction support through route fetching with Google Maps fallback
- Busyness overlay showing whether nearby areas are not busy, as usual, or busier
- Authentication-aware flows for login, signup, saved events, and bookings
- Student profile and settings screens

### Partner / Organiser Experience

- Partner dashboard for event organisers
- Create and manage event listings
- Manage venues and organisation-owned events
- View listing status, capacity, spots remaining, bookings, and revenue
- Analytics page for organiser performance metrics
- Partner settings page for account and organisation management
- Shared booking view for tracking event reservations

### Backend & Platform Features

- FastAPI REST API for profiles, events, venues, organisations, bookings, saved events, payments, feedback, busyness, and dashboard data
- Supabase Auth JWT verification for protected endpoints
- PostgreSQL database hosted through Supabase
- SQLAlchemy models and schema validation with Pydantic
- Event discovery API with optional latitude/longitude distance calculation
- Booking lifecycle support, including confirmed and cancelled states
- Saved-event endpoints for authenticated users
- Organisation and membership management for partner users
- Stripe checkout integration for paid events
- Stripe webhook handling for payment completion, expiry, and failure
- Feedback endpoint for collecting user input
- Busyness API designed for local demand signals and spatial analytics
- Database migrations tracked in `backend/supabase/migrations`
- Automated backend tests for health checks, event contracts, schemas, organisations, venues, bookings, and payments

### Mobile, Web, and Data

- Flutter mobile app targeting iOS, Android, and web
- React + Vite web frontend for student and partner workflows
- Leaflet-based interactive maps on the web frontend
- Shared API patterns between mobile and web clients
- Data processing scripts for normalised spatial feature tables
- Test fixtures for the data pipeline

## Links

- **Web app (live):** https://fromo-website.onrender.com/
- **Mobile app (live):** https://fromomobile.netlify.app/#/map
- **Project board (Linear):** https://linear.app/research-semester-group-9/team/RES/overview
- **Google Drive as supporting documentation:** all related documents for each week and sprint — https://drive.google.com/drive/u/0/folders/1QGeYSQVy4dyRFpbVilOwfxC7y5JIhBQO

---

## Project Structure

```
FROMO/
├── mobile/     # Flutter mobile app (iOS, Android, Web)
├── backend/    # FastAPI backend
├── web/        # Web frontend
├── data/       # Data scripts
└── infra/      # Infrastructure config
```

---

## Prerequisites

Make sure you have the following installed before starting:

| Tool | Version | Install |
|------|---------|---------|
| Flutter | 3.44+ | [flutter.dev](https://flutter.dev/docs/get-started/install) |
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Chrome | any | [google.com/chrome](https://www.google.com/chrome/) |

After installing Flutter, run `flutter doctor` and make sure there are no critical errors.

---

## Backend Setup

**1. Go to the backend folder:**
```bash
cd backend
```

**2. Install dependencies:**
```bash
uv sync
```

**3. Create your `.env` file:**
```bash
cp .env.example .env
```

Then open `.env` and fill in the values (ask a teammate for the credentials):
```
DATABASE_URL=postgresql://postgres:<password>@db.seqpmxiutifcrbitmajh.supabase.co:5432/postgres
SUPABASE_URL=https://seqpmxiutifcrbitmajh.supabase.co
SUPABASE_PUBLISHABLE_KEY=<anon key>
```

**4. Start the server:**
```bash
uv run uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can explore all endpoints at `http://localhost:8000/docs`.

---

## Web Setup

**1. Go to the web folder:**
```bash
cd web
```

**2. Install dependencies:**
```bash
npm install
```

**3. Create your `.env` file:**
```bash
cp .env.example .env
```

Then open `.env` and fill in the values (ask a teammate for the Supabase credentials):
```
VITE_SUPABASE_URL=https://seqpmxiutifcrbitmajh.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key>
VITE_API_BASE_URL=/api
```

`VITE_API_BASE_URL` should stay as `/api` — the Vite dev server proxies it to the backend on port 8000, which avoids CORS errors. `VITE_ORS_API_KEY` is optional and only enables in-app walking directions; without it, "Directions" opens Google Maps instead.

**4. Start the dev server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

> Note: The backend must be running before you start the web app, otherwise events won't load.

---

## Mobile Setup

**1. Go to the mobile folder:**
```bash
cd mobile
```

**2. Install Flutter dependencies:**
```bash
flutter pub get
```

**3. Run on Chrome (recommended for development):**
```bash
flutter run -d chrome
```

**4. Run on Android emulator:**
```bash
flutter run -d android
```

If you've never set up Android before, do this once first:

1. Install **Android Studio**, then the SDK + a system image — either via Android
   Studio's SDK Manager / Device Manager, or the command line:
   ```bash
   brew install --cask android-commandlinetools           # macOS
   export ANDROID_HOME="$HOME/Library/Android/sdk"         # add this to ~/.zshrc
   sdkmanager "platform-tools" "emulator" "cmdline-tools;latest" \
              "platforms;android-36" "build-tools;36.0.0" \
              "system-images;android-35;google_apis;arm64-v8a"
   avdmanager create avd -n Pixel_7_API_35 \
              -k "system-images;android-35;google_apis;arm64-v8a" -d pixel_7
   flutter config --android-sdk "$ANDROID_HOME"
   ```
2. Start the emulator, then run:
   ```bash
   emulator -avd Pixel_7_API_35
   flutter run -d android
   ```
3. **Type with your computer keyboard:** set `hw.keyboard=yes` in
   `~/.android/avd/<AVD>.avd/config.ini`, then restart the emulator.
4. **Test NYC events/heatmap:** seed data lives in Manhattan, so set the emulator
   location (Extended controls `...` → Location) to e.g. `40.7580, -73.9855`.

> Run `flutter doctor` and confirm the Android toolchain shows a green check.

> Note: The backend must be running before you start the mobile app, otherwise events won't load.

---

## Supabase Credentials

The Supabase anon key and project URL are already hardcoded in `mobile/lib/core/constants.dart` — no extra setup needed for the mobile app.

For the backend `.env`, ask the project owner for the `DATABASE_URL` password.

---

## Common Issues

**Events not loading?**
- Make sure the backend is running on port 8000
- Check `http://localhost:8000/docs` to confirm the API is up

**Location permission popup on Chrome?**
- You can click "Block" — the app will still show all events
- Location is used to show distance and center the map; it is not required

**`flutter doctor` shows errors?**
- Chrome errors can be ignored if you're only running on web
- Android/iOS errors can be ignored if you're only testing on Chrome

**Map shows the wrong city / no events near you?**
- The map centers on your device location. On an emulator, set the location to
  Manhattan (`40.7580, -73.9855`) since that's where the seed data is.

**Heatmap circles look like demo data?**
- They are. Until the backend `/busyness` tables are populated, the app falls back
  to a small built-in sample (`_sampleBusynessAreas` in `map_providers.dart`).
  Delete that fallback once real busyness data is available.
