# FROMO
FROMO (Free from FOMO) — A real-time, location-based last-minute event radar for students. Built on NYC NTA spatial demand models to combat youth social isolation.

## Links

- **Web app (live):** https://fromo-website.onrender.com/
- **Mobile app (live):** https://fromomobile.netlify.app/#/map
- **Project board (Linear):** https://linear.app/research-semester-group-9/team/RES/overview
- **Google Drive:** all related documents for each week and sprint — https://drive.google.com/drive/u/0/folders/1QGeYSQVy4dyRFpbVilOwfxC7y5JIhBQO

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
