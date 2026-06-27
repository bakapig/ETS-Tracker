# ETS Live Malaysia

Real-time **ETS (Electric Train Service)** arrivals and live train map for Malaysia, built on the official [Malaysia Open API](https://developer.data.gov.my/realtime-api/gtfs-realtime) KTMB GTFS feeds.

## What's included (MVP)

| Layer | Stack | Features |
|-------|-------|----------|
| **Backend** | Python FastAPI | GTFS static schedule, GTFS-RT vehicle positions (30s poll), ETA/delay estimate, REST API |
| **Web** | Next.js + Tailwind + Leaflet | Station search, next arrivals, live map, AdSense placeholders |
| **Android** | Flutter + flutter_map + AdMob | Same features as web, native Android app |

## Architecture

```
Malaysia Open API (GTFS Static + GTFS-RT)
        ↓  (backend polls every 30s)
   FastAPI + in-memory cache
        ↓
   Next.js Web  →  Flutter Android + AdMob
```

**Important:** Clients never call `api.data.gov.my` directly — the backend caches data and adds ETA logic.

## Quick start (local)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Web

```powershell
cd web
copy .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

### 3. Android

```powershell
cd mobile
flutter pub get
flutter run
```

See [mobile/README.md](mobile/README.md) for emulator vs physical device API URLs.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service status |
| GET | `/api/stations?q=ipoh` | Search ETS stations |
| GET | `/api/stations/{stop_id}/arrivals` | Next ETS arrivals + delay |
| GET | `/api/vehicles` | Live train positions |
| POST | `/api/admin/refresh-static` | Re-download GTFS ZIP |

## Data sources

- Static schedule: `https://api.data.gov.my/gtfs-static/ktmb/`
- Live positions: `https://api.data.gov.my/gtfs-realtime/vehicle-position/ktmb/` (updates ~30s)

## Monetisation

1. **Web** — Google AdSense via `AdBanner` (set env vars in `web/.env.local`; see `web/.env.local.example`). Dynamic `ads.txt` is served at `/ads.txt`.
2. **Android** — AdMob adaptive banners via `google_mobile_ads` (`ADMOB_APP_ID` in `gradle.properties`, banner units via `--dart-define`; see `mobile/README.md`).
3. **Premium** — RM4.90/mo: no ads, push delay alerts (Firebase Cloud Messaging).

## Android app

Flutter app in `mobile/` — calls the same REST API as the web client.

```powershell
cd mobile
flutter run
# physical device on LAN:
flutter run --dart-define=API_BASE_URL=http://YOUR_PC_IP:8000
```

Details: [mobile/README.md](mobile/README.md)

## Deploy

```powershell
docker compose up --build
```

- Backend: http://localhost:8000  
- Web: http://localhost:3000  

For production, deploy backend (Railway/Fly.io/VM) and web (Vercel) with `NEXT_PUBLIC_API_URL` pointing to your API.

## Limitations (MVP)

- GTFS-RT currently provides **vehicle position only** (no official trip updates until ~2026).
- Delay/ETA is **estimated** from GPS + schedule shape — not KTMB official.
- KL has two nearby stops: **KUALA LUMPUR** (`19000`) and **KL SENTRAL** (`19100`) — search both for full coverage.

## License

MIT — GTFS data © respective operators; check [data.gov.my terms](https://developer.data.gov.my) for commercial use.
