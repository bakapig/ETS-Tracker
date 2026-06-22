from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from google.transit import gtfs_realtime_pb2

from app.config import settings
from app.models import Vehicle

MYT = ZoneInfo("Asia/Kuala_Lumpur")


class RealtimeStore:
    def __init__(self) -> None:
        self.vehicles: list[Vehicle] = []
        self.trip_index: dict[str, dict] = {}
        self.last_fetch: datetime | None = None
        self.last_error: str | None = None

    def get_live_trips(self) -> dict[str, dict]:
        return dict(self.trip_index)


realtime_store = RealtimeStore()


def _decode_feed(data: bytes) -> gtfs_realtime_pb2.FeedMessage:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed


async def fetch_vehicle_positions() -> None:
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get(settings.gtfs_realtime_url)
            response.raise_for_status()
            data = response.content

        feed = _decode_feed(data)
        vehicles: list[Vehicle] = []
        trip_index: dict[str, dict] = {}

        for entity in feed.entity:
            if not entity.HasField("vehicle"):
                continue
            vp = entity.vehicle
            pos = vp.position if vp.HasField("position") else None
            trip = vp.trip if vp.HasField("trip") else None
            if not pos:
                continue

            trip_id = trip.trip_id if trip and trip.trip_id else None
            route_id = trip.route_id if trip and trip.route_id else None
            speed_kmh = pos.speed * 3.6 if pos.speed else None

            vehicle = Vehicle(
                vehicle_id=entity.id or (vp.vehicle.id if vp.HasField("vehicle") else "unknown"),
                trip_id=trip_id,
                route_id=route_id,
                label=vp.vehicle.label if vp.HasField("vehicle") and vp.vehicle.label else None,
                latitude=pos.latitude,
                longitude=pos.longitude,
                bearing=pos.bearing if pos.bearing else None,
                speed_kmh=speed_kmh,
                timestamp=vp.timestamp if vp.timestamp else None,
                occupancy_status=(
                    gtfs_realtime_pb2.VehiclePosition.OccupancyStatus.Name(vp.occupancy_status)
                    if vp.HasField("occupancy_status")
                    else None
                ),
            )
            vehicles.append(vehicle)

            if trip_id:
                trip_index[trip_id] = {
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "label": vehicle.label,
                    "latitude": vehicle.latitude,
                    "longitude": vehicle.longitude,
                    "bearing": vehicle.bearing,
                    "speed_kmh": vehicle.speed_kmh,
                    "timestamp": vehicle.timestamp,
                }

        realtime_store.vehicles = vehicles
        realtime_store.trip_index = trip_index
        realtime_store.last_fetch = datetime.now(MYT)
        realtime_store.last_error = None
    except Exception as exc:  # noqa: BLE001 — keep worker alive
        realtime_store.last_error = str(exc)


def filter_ets_vehicles(vehicles: list[Vehicle], ets_trip_ids: set[str]) -> list[Vehicle]:
    filtered = []
    for v in vehicles:
        if v.trip_id and v.trip_id in ets_trip_ids:
            filtered.append(v)
            continue
        # Include trains whose label looks like ETS (e.g. ETS9234)
        if v.label and "ETS" in v.label.upper():
            filtered.append(v)
    return filtered
