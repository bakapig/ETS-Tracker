from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import settings

MYT = ZoneInfo("Asia/Kuala_Lumpur")


@dataclass
class StopRecord:
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float


@dataclass
class RouteRecord:
    route_id: str
    route_short_name: str
    route_long_name: str


@dataclass
class TripRecord:
    route_id: str
    service_id: str
    trip_id: str
    direction_id: int


@dataclass
class StopTimeRecord:
    trip_id: str
    arrival_time: str
    departure_time: str
    stop_id: str
    stop_sequence: int
    shape_dist_traveled: float | None = None


@dataclass
class CalendarRecord:
    service_id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start_date: date
    end_date: date


ETS_ROUTE_ID = "ETS"


@dataclass
class GtfsDataset:
    stops: dict[str, StopRecord] = field(default_factory=dict)
    routes: dict[str, RouteRecord] = field(default_factory=dict)
    trips: dict[str, TripRecord] = field(default_factory=dict)
    stop_times_by_trip: dict[str, list[StopTimeRecord]] = field(default_factory=dict)
    stop_times_by_stop: dict[str, list[StopTimeRecord]] = field(default_factory=dict)
    calendar: dict[str, CalendarRecord] = field(default_factory=dict)
    ets_trip_ids: frozenset[str] = field(default_factory=frozenset)
    ets_stop_ids: frozenset[str] = field(default_factory=frozenset)
    trip_destinations: dict[str, str] = field(default_factory=dict)
    loaded_at: datetime | None = None


def _build_indexes(dataset: GtfsDataset) -> None:
    ets_trips: set[str] = set()
    ets_stops: set[str] = set()
    destinations: dict[str, str] = {}

    for trip_id, trip in dataset.trips.items():
        times = dataset.stop_times_by_trip.get(trip_id, [])
        if not times:
            continue
        last_stop_id = times[-1].stop_id
        stop = dataset.stops.get(last_stop_id)
        destinations[trip_id] = stop.stop_name if stop else last_stop_id
        if trip.route_id != ETS_ROUTE_ID:
            continue
        ets_trips.add(trip_id)
        for st in times:
            ets_stops.add(st.stop_id)

    dataset.ets_trip_ids = frozenset(ets_trips)
    dataset.ets_stop_ids = frozenset(ets_stops)
    dataset.trip_destinations = destinations


def parse_gtfs_time(time_str: str, base_date: date) -> datetime:
    """Parse GTFS time (supports hours >= 24) into MYT datetime."""
    parts = time_str.strip().split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) > 2 else 0
    day_offset = hours // 24
    hour = hours % 24
    dt = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        hour,
        minutes,
        seconds,
        tzinfo=MYT,
    )
    if day_offset:
        dt += timedelta(days=day_offset)
    return dt


def service_runs_on(calendar: CalendarRecord, target: date) -> bool:
    if target < calendar.start_date:
        return False
    weekday = target.weekday()
    flags = [
        calendar.monday,
        calendar.tuesday,
        calendar.wednesday,
        calendar.thursday,
        calendar.friday,
        calendar.saturday,
        calendar.sunday,
    ]
    if not flags[weekday]:
        return False
    if target <= calendar.end_date:
        return True
    # Stale GTFS calendar — still honour weekday flags until feed refreshes.
    return True


def calendar_stale(dataset: GtfsDataset, today: date | None = None) -> bool:
    today = today or datetime.now(MYT).date()
    if not dataset.calendar:
        return True
    latest_end = max(c.end_date for c in dataset.calendar.values())
    return latest_end < today


def _read_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def load_gtfs_from_zip_bytes(data: bytes) -> GtfsDataset:
    dataset = GtfsDataset()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = {name.lower().split("/")[-1]: name for name in zf.namelist()}

        def read(name: str) -> str:
            return zf.read(names[name.lower()]).decode("utf-8-sig")

        for row in _read_csv(read("stops.txt")):
            stop = StopRecord(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                stop_lat=float(row["stop_lat"]),
                stop_lon=float(row["stop_lon"]),
            )
            dataset.stops[stop.stop_id] = stop

        for row in _read_csv(read("routes.txt")):
            route = RouteRecord(
                route_id=row["route_id"],
                route_short_name=row.get("route_short_name", ""),
                route_long_name=row.get("route_long_name", ""),
            )
            dataset.routes[route.route_id] = route

        for row in _read_csv(read("trips.txt")):
            trip = TripRecord(
                route_id=row["route_id"],
                service_id=row["service_id"],
                trip_id=row["trip_id"],
                direction_id=int(row.get("direction_id") or 0),
            )
            dataset.trips[trip.trip_id] = trip

        for row in _read_csv(read("stop_times.txt")):
            shape = row.get("shape_dist_traveled")
            st = StopTimeRecord(
                trip_id=row["trip_id"],
                arrival_time=row["arrival_time"],
                departure_time=row["departure_time"],
                stop_id=row["stop_id"],
                stop_sequence=int(row["stop_sequence"]),
                shape_dist_traveled=float(shape) if shape else None,
            )
            dataset.stop_times_by_trip.setdefault(st.trip_id, []).append(st)
            dataset.stop_times_by_stop.setdefault(st.stop_id, []).append(st)

        for trip_id, times in dataset.stop_times_by_trip.items():
            times.sort(key=lambda t: t.stop_sequence)

        for row in _read_csv(read("calendar.txt")):
            cal = CalendarRecord(
                service_id=row["service_id"],
                monday=row["monday"] == "1",
                tuesday=row["tuesday"] == "1",
                wednesday=row["wednesday"] == "1",
                thursday=row["thursday"] == "1",
                friday=row["friday"] == "1",
                saturday=row["saturday"] == "1",
                sunday=row["sunday"] == "1",
                start_date=datetime.strptime(row["start_date"], "%Y%m%d").date(),
                end_date=datetime.strptime(row["end_date"], "%Y%m%d").date(),
            )
            dataset.calendar[cal.service_id] = cal

    _build_indexes(dataset)
    dataset.loaded_at = datetime.now(MYT)
    return dataset


async def download_gtfs_static() -> bytes:
    from app.http_client import get_http_client

    client = get_http_client()
    response = await client.get(settings.gtfs_static_url)
    response.raise_for_status()
    return response.content


def save_gtfs_cache(data: bytes) -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    path = settings.data_dir / "ktmb_gtfs.zip"
    path.write_bytes(data)
    return path


def load_gtfs_cache() -> bytes | None:
    path = settings.data_dir / "ktmb_gtfs.zip"
    if path.exists():
        return path.read_bytes()
    return None
