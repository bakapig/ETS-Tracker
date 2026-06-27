from __future__ import annotations

from app.gtfs.loader import GtfsDataset
from app.gtfs.trip_numbers import infer_train_class, normalize_speed_kmh, resolve_service_number
from app.models import Vehicle

# route_id from static GTFS → category key
ROUTE_CATEGORY: dict[str, str] = {
    "ETS": "ets",
    "100_47300": "komuter",
    "100_9000": "komuter",
    "KA15_KD19": "komuter",
    "KC05_KB18": "komuter",
    "ERT": "intercity",
    "ES": "intercity",
    "SH": "shuttle",
    "ST": "shuttle",
}

CATEGORY_LABELS: dict[str, str] = {
    "ets": "ETS",
    "komuter": "KTM Komuter",
    "intercity": "Intercity",
    "shuttle": "Intercity Shuttle",
    "other": "Other",
}

# Sort routes in map legend / list
ROUTE_SORT_ORDER: dict[str, int] = {
    "ETS": 0,
    "100_47300": 10,
    "100_9000": 11,
    "KA15_KD19": 12,
    "KC05_KB18": 13,
    "ERT": 20,
    "ES": 21,
    "SH": 30,
    "ST": 31,
}

CATEGORY_ORDER = ("ets", "komuter", "intercity", "shuttle", "other")


def format_route_display_name(
    short_name: str | None,
    long_name: str | None,
) -> str | None:
    if short_name and long_name:
        return f"{short_name} - {long_name}"
    return short_name or long_name


def route_category(route_id: str | None) -> str:
    if not route_id:
        return "other"
    return ROUTE_CATEGORY.get(route_id, "other")


def resolve_route_id(dataset: GtfsDataset | None, trip_id: str | None) -> str | None:
    if not dataset or not trip_id:
        return None
    trip = dataset.trips.get(trip_id)
    return trip.route_id if trip else None


def enrich_vehicle(vehicle: Vehicle, dataset: GtfsDataset | None) -> Vehicle:
    resolved_route = vehicle.route_id or resolve_route_id(dataset, vehicle.trip_id)
    category = route_category(resolved_route)

    short_name: str | None = None
    long_name: str | None = None
    if dataset and resolved_route:
        route = dataset.routes.get(resolved_route)
        if route:
            short_name = route.route_short_name
            long_name = route.route_long_name

    service_number = resolve_service_number(vehicle.trip_id, resolved_route)
    train_class, train_class_label = infer_train_class(vehicle.label, category)
    speed_kmh = normalize_speed_kmh(vehicle.speed_kmh)
    route_display_name = format_route_display_name(short_name, long_name)

    return vehicle.model_copy(
        update={
            "route_id": resolved_route,
            "route_category": category,
            "route_short_name": short_name,
            "route_long_name": long_name,
            "route_display_name": route_display_name,
            "service_number": service_number,
            "train_class": train_class,
            "train_class_label": train_class_label,
            "speed_kmh": speed_kmh,
        }
    )
