# FROMO
FROMO (Free from FOMO) — A real-time, location-based last-minute event radar for students. Built on NYC NTA spatial demand models to combat youth social isolation.

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

**4. Run on Android emulator** (make sure Android Studio + emulator are set up):
```bash
flutter run -d android
```

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
