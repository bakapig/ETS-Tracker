from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.gtfs.loader import (
    GtfsDataset,
    parse_gtfs_time,
    service_runs_on,
)
from app.models import Arrival

MYT = ZoneInfo("Asia/Kuala_Lumpur")
ETS_ROUTE_ID = "ETS"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _trip_destination(dataset: GtfsDataset, trip_id: str) -> str:
    times = dataset.stop_times_by_trip.get(trip_id, [])
    if not times:
        return "Unknown"
    last_stop_id = times[-1].stop_id
    stop = dataset.stops.get(last_stop_id)
    return stop.stop_name if stop else last_stop_id


def _delay_status(delay_minutes: int | None) -> str:
    if delay_minutes is None:
        return "scheduled"
    if delay_minutes <= -2:
        return "early"
    if delay_minutes >= 3:
        return "delayed"
    return "on_time"


def get_ets_stations(dataset: GtfsDataset) -> list[str]:
    stop_ids: set[str] = set()
    for trip_id, trip in dataset.trips.items():
        if trip.route_id != ETS_ROUTE_ID:
            continue
        for st in dataset.stop_times_by_trip.get(trip_id, []):
            stop_ids.add(st.stop_id)
    return sorted(stop_ids, key=lambda sid: dataset.stops[sid].stop_name if sid in dataset.stops else sid)


def search_stations(dataset: GtfsDataset, query: str, ets_only: bool = True) -> list:
    q = query.strip().lower()
    ets_stops = set(get_ets_stations(dataset)) if ets_only else None
    results = []
    for stop in dataset.stops.values():
        if ets_stops is not None and stop.stop_id not in ets_stops:
            continue
        if not q or q in stop.stop_name.lower() or q in stop.stop_id:
            results.append(stop)
    results.sort(key=lambda s: s.stop_name)
    return results[:30]


def get_next_arrivals(
    dataset: GtfsDataset,
    stop_id: str,
    *,
    route_id: str = ETS_ROUTE_ID,
    limit: int = 10,
    now: datetime | None = None,
    live_trips: dict[str, dict] | None = None,
) -> list[Arrival]:
    now = now or datetime.now(MYT)
    today = now.date()
    live_trips = live_trips or {}
    candidates: list[tuple[datetime, Arrival]] = []

    for st in dataset.stop_times_by_stop.get(stop_id, []):
        trip = dataset.trips.get(st.trip_id)
        if not trip or trip.route_id != route_id:
            continue
        cal = dataset.calendar.get(trip.service_id)
        if not cal or not service_runs_on(cal, today):
            continue

        route = dataset.routes.get(trip.route_id)
        scheduled_arr = parse_gtfs_time(st.arrival_time, today)
        scheduled_dep = parse_gtfs_time(st.departure_time, today)

        # Include trains in the next 12 hours, or slightly past (for delay display)
        if scheduled_arr < now - timedelta(minutes=30):
            continue
        if scheduled_arr > now + timedelta(hours=12):
            continue

        live = live_trips.get(st.trip_id)
        delay_minutes: int | None = None
        estimated_arrival: str | None = None
        is_live = False
        vehicle_label = None
        status = "scheduled"

        if live:
            is_live = True
            vehicle_label = live.get("label")
            delay_minutes = _estimate_delay_minutes(dataset, st.trip_id, stop_id, live, scheduled_arr, now)
            if delay_minutes is not None:
                eta = scheduled_arr + timedelta(minutes=delay_minutes)
                estimated_arrival = eta.strftime("%H:%M")
                status = _delay_status(delay_minutes)
            else:
                status = "live"

        arrival = Arrival(
            trip_id=st.trip_id,
            route_short_name=route.route_short_name if route else route_id,
            route_long_name=route.route_long_name if route else "",
            destination=_trip_destination(dataset, st.trip_id),
            scheduled_arrival=scheduled_arr.strftime("%H:%M"),
            scheduled_departure=scheduled_dep.strftime("%H:%M"),
            estimated_arrival=estimated_arrival,
            delay_minutes=delay_minutes,
            status=status,
            is_live=is_live,
            vehicle_label=vehicle_label,
        )
        sort_time = scheduled_arr
        if delay_minutes is not None:
            sort_time = scheduled_arr + timedelta(minutes=delay_minutes)
        candidates.append((sort_time, arrival))

    candidates.sort(key=lambda x: x[0])
    return [a for _, a in candidates[:limit]]


def _estimate_delay_minutes(
    dataset: GtfsDataset,
    trip_id: str,
    target_stop_id: str,
    live: dict,
    scheduled_arrival: datetime,
    now: datetime,
) -> int | None:
    """Rough ETA delay from vehicle GPS vs schedule shape distance."""
    times = dataset.stop_times_by_trip.get(trip_id, [])
    if not times:
        return None

    target_idx = next((i for i, t in enumerate(times) if t.stop_id == target_stop_id), None)
    if target_idx is None:
        return None

    target_stop = dataset.stops.get(target_stop_id)
    if not target_stop:
        return None

    lat = live.get("latitude")
    lon = live.get("longitude")
    if lat is None or lon is None:
        return None

    # Find nearest stop sequence along the trip
    best_idx = 0
    best_dist = float("inf")
    for i, st in enumerate(times):
        stop = dataset.stops.get(st.stop_id)
        if not stop:
            continue
        dist = _haversine_km(lat, lon, stop.stop_lat, stop.stop_lon)
        if dist < best_dist:
            best_dist = dist
            best_idx = i

    if best_idx >= target_idx:
        # Train already passed or at target — compare clock time
        delta = (now - scheduled_arrival).total_seconds() / 60
        return max(0, int(round(delta)))

    # Estimate remaining travel from shape distance ratio
    target_shape = times[target_idx].shape_dist_traveled
    current_shape = times[best_idx].shape_dist_traveled
    if target_shape is None or current_shape is None or target_shape <= current_shape:
        km_remaining = _haversine_km(lat, lon, target_stop.stop_lat, target_stop.stop_lon)
        speed = live.get("speed_kmh") or 80.0
        if speed < 5:
            speed = 80.0
        minutes_remaining = (km_remaining / speed) * 60
        eta = now + timedelta(minutes=minutes_remaining)
        delay = (eta - scheduled_arrival).total_seconds() / 60
        return int(round(delay))

    remaining_km = target_shape - current_shape
    speed = live.get("speed_kmh") or 90.0
    if speed < 5:
        speed = 90.0
    minutes_remaining = (remaining_km / speed) * 60
    eta = now + timedelta(minutes=minutes_remaining)
    delay = (eta - scheduled_arrival).total_seconds() / 60
    return int(round(delay))
