# ETS Live Malaysia — Android

Flutter Android app for real-time ETS train arrivals and live map. Uses the same FastAPI backend as the web app.

## Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (stable)
- Android Studio with Android SDK & emulator (or a physical device with USB debugging)
- Backend running (see repo root `README.md`)

## Quick start

### 1. Start the backend

```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### 2. Run the app

**Android emulator** (default API URL `http://10.0.2.2:8000`):

```powershell
cd mobile
flutter pub get
flutter run
```

**Physical device** on the same Wi‑Fi — use your PC's LAN IP:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

**Production API:**

```powershell
flutter run --dart-define=API_BASE_URL=https://your-api.example.com
```

## Features

| Feature | Implementation |
|---------|----------------|
| Station search | `GET /api/stations?q=…` |
| Next arrivals | `GET /api/stations/{id}/arrivals` (auto-refresh 30s) |
| Live map | `flutter_map` + OpenStreetMap, `GET /api/vehicles` |
| Ads | AdMob adaptive banners via `google_mobile_ads` |

## AdMob setup

1. Create an app in [AdMob](https://admob.google.com) and note the **App ID** (`ca-app-pub-…~…`).
2. Create two **Banner** ad units (top + bottom) and note their **Ad unit IDs**.
3. Set the App ID in `android/gradle.properties` (see `android/gradle.properties.example`):

   ```properties
   ADMOB_APP_ID=ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY
   ```

4. Pass banner unit IDs at build/run time:

   ```powershell
   flutter run --dart-define=ADMOB_BANNER_TOP=ca-app-pub-…/… --dart-define=ADMOB_BANNER_BOTTOM=ca-app-pub-…/…
   ```

Without step 3–4 the app uses [Google's official test IDs](https://developers.google.com/admob/android/test-ads) (safe for development).

## Release build

```powershell
flutter build apk --release `
  --dart-define=API_BASE_URL=https://your-api.example.com `
  --dart-define=ADMOB_BANNER_TOP=ca-app-pub-…/… `
  --dart-define=ADMOB_BANNER_BOTTOM=ca-app-pub-…/…
```

APK output: `build/app/outputs/flutter-apk/app-release.apk`

Before publishing:

1. Set `ADMOB_APP_ID` in `android/gradle.properties` and banner `--dart-define` values above
2. Set `android:usesCleartextTraffic="false"` if API is HTTPS-only
3. Configure app signing in `android/app/build.gradle.kts`

## Project layout

```
lib/
  config/api_config.dart    # API base URL (dart-define)
  config/admob_config.dart  # AdMob banner unit IDs (dart-define)
  models/                   # Station, Arrival, Vehicle
  services/api_client.dart  # REST client
  screens/home_screen.dart  # Main UI
  widgets/                  # Search, arrivals, map, ads
```
