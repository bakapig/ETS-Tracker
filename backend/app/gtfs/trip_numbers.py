from __future__ import annotations

import json
import re

from app.config import settings

DATA_FILE = settings.data_dir / "trip_service_numbers.json"

# Prefix letters: EG=Gold, EX=Express, EP=Platinum (KTMB ETS public numbering).
ETS_PREFIX_BY_FIRST_DIGIT = {
    "9": "EG",  # most gold / mixed 9xxx
}

TRAIN_CLASS_BY_LABEL: list[tuple[str, str, str]] = [
    ("ETS", "ets", "Class 93/2 - ETS"),
    ("EMU", "komuter_83", "Class 83 - Komuter"),
    ("SCS", "komuter_92", "Class 92 - Komuter"),
    ("DMU", "dmu_61", "Class 61 - DMU"),
]

_trip_lookup: dict[str, dict] | None = None


def load_trip_lookup() -> dict[str, dict]:
    global _trip_lookup
    if _trip_lookup is not None:
        return _trip_lookup

    if DATA_FILE.exists():
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        _trip_lookup = raw if isinstance(raw, dict) else {}
    else:
        _trip_lookup = {}
    return _trip_lookup


def reload_trip_lookup() -> None:
    global _trip_lookup
    _trip_lookup = None
    load_trip_lookup()


def _trip_id_candidates(trip_id: str) -> list[str]:
    candidates = [trip_id]
    for prefix in ("weekday_", "weekend_"):
        if trip_id.startswith(prefix):
            candidates.append(trip_id[len(prefix) :])
    if m := re.match(r"^\d{8}_(\d+_.+)$", trip_id):
        candidates.append(m.group(1))
    if m := re.match(r"^\d+_(.+)$", trip_id):
        candidates.append(m.group(1))
    # preserve order, dedupe
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _guess_ets_service(trip_id: str, route_id: str | None) -> str | None:
    if route_id != "ETS" and not trip_id.isdigit():
        return None
    numeric = re.sub(r"\D", "", trip_id)
    if len(numeric) < 4:
        return None
    # Unmapped ETS: best-effort EG + id (user can fix in trip_service_numbers.json)
    return f"EG{numeric[-4:]}"


def resolve_service_number(
    trip_id: str | None,
    route_id: str | None = None,
) -> str | None:
    if not trip_id:
        return None

    lookup = load_trip_lookup()
    for candidate in _trip_id_candidates(trip_id):
        entry = lookup.get(candidate)
        if entry and entry.get("service_number"):
            return entry["service_number"]

    if route_id == "ETS":
        return _guess_ets_service(trip_id, route_id)

    return trip_id


def infer_train_class(
    label: str | None,
    route_category: str | None = None,
) -> tuple[str, str]:
    if label:
        upper = label.upper()
        for prefix, asset_key, display in TRAIN_CLASS_BY_LABEL:
            if upper.startswith(prefix):
                return asset_key, display

    if route_category == "ets":
        return "ets", "Class 93/2 - ETS"
    if route_category == "komuter":
        return "komuter_83", "Class 83 - Komuter"
    if route_category == "shuttle":
        return "dmu_61", "Class 61 - DMU"
    if route_category == "intercity":
        return "intercity", "Intercity"
    return "default", "KTMB"


def normalize_speed_kmh(raw: float | None) -> float | None:
    """KTMB GTFS-RT reports speed in km/h (not m/s per GTFS spec)."""
    if raw is None:
        return None
    speed = float(raw)
    # Legacy bug guard: values >200 were wrongly multiplied by 3.6
    if speed > 200:
        speed = round(speed / 3.6, 1)
    if speed < 0 or speed > 200:
        return None
    return round(speed, 1)
