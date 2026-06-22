from fastapi import APIRouter, HTTPException, Query

from app.gtfs.realtime import filter_ets_vehicles, realtime_store
from app.gtfs.schedule import get_next_arrivals, search_stations
from app.models import Arrival, HealthResponse, Station, Vehicle
from app.services.state import app_state

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    ds = app_state.dataset
    ets_count = len(app_state.ets_trip_ids) if ds else 0
    return HealthResponse(
        status="ok" if ds else "loading",
        gtfs_loaded=ds is not None,
        stations_count=len(ds.stops) if ds else 0,
        ets_trips_count=ets_count,
        vehicles_count=len(realtime_store.vehicles),
        last_realtime_fetch=(
            realtime_store.last_fetch.isoformat() if realtime_store.last_fetch else None
        ),
        last_static_fetch=(
            app_state.last_static_fetch.isoformat() if app_state.last_static_fetch else None
        ),
    )


@router.get("/stations", response_model=list[Station])
async def list_stations(
    q: str = Query("", description="Search by station name or ID"),
    ets_only: bool = Query(True, description="Only ETS-served stations"),
) -> list[Station]:
    if not app_state.dataset:
        raise HTTPException(503, "GTFS data not loaded yet")
    stops = search_stations(app_state.dataset, q, ets_only=ets_only)
    return [
        Station(
            stop_id=s.stop_id,
            stop_name=s.stop_name,
            stop_lat=s.stop_lat,
            stop_lon=s.stop_lon,
        )
        for s in stops
    ]


@router.get("/stations/{stop_id}", response_model=Station)
async def get_station(stop_id: str) -> Station:
    if not app_state.dataset:
        raise HTTPException(503, "GTFS data not loaded yet")
    stop = app_state.dataset.stops.get(stop_id)
    if not stop:
        raise HTTPException(404, "Station not found")
    return Station(
        stop_id=stop.stop_id,
        stop_name=stop.stop_name,
        stop_lat=stop.stop_lat,
        stop_lon=stop.stop_lon,
    )


@router.get("/stations/{stop_id}/arrivals", response_model=list[Arrival])
async def station_arrivals(
    stop_id: str,
    limit: int = Query(10, ge=1, le=30),
    route: str = Query("ETS", description="Route ID filter"),
) -> list[Arrival]:
    if not app_state.dataset:
        raise HTTPException(503, "GTFS data not loaded yet")
    if stop_id not in app_state.dataset.stops:
        raise HTTPException(404, "Station not found")
    return get_next_arrivals(
        app_state.dataset,
        stop_id,
        route_id=route,
        limit=limit,
        live_trips=realtime_store.get_live_trips(),
    )


@router.get("/vehicles", response_model=list[Vehicle])
async def list_vehicles(
    ets_only: bool = Query(True, description="Filter to ETS trains only"),
) -> list[Vehicle]:
    vehicles = realtime_store.vehicles
    if ets_only:
        vehicles = filter_ets_vehicles(vehicles, app_state.ets_trip_ids)
    return vehicles


@router.post("/admin/refresh-static")
async def refresh_static() -> dict:
    await app_state.load_static(force_download=True)
    return {"status": "ok", "stations": len(app_state.dataset.stops) if app_state.dataset else 0}
