from pydantic import BaseModel, Field


class Station(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float


class Arrival(BaseModel):
    trip_id: str
    route_short_name: str
    route_long_name: str
    destination: str
    scheduled_arrival: str
    scheduled_departure: str
    estimated_arrival: str | None = None
    delay_minutes: int | None = None
    status: str = Field(description="on_time | delayed | early | scheduled | live")
    is_live: bool = False
    vehicle_label: str | None = None


class Vehicle(BaseModel):
    vehicle_id: str
    trip_id: str | None = None
    route_id: str | None = None
    label: str | None = None
    latitude: float
    longitude: float
    bearing: float | None = None
    speed_kmh: float | None = None
    timestamp: int | None = None
    occupancy_status: str | None = None


class HealthResponse(BaseModel):
    status: str
    gtfs_loaded: bool
    stations_count: int
    ets_trips_count: int
    vehicles_count: int
    last_realtime_fetch: str | None
    last_static_fetch: str | None
