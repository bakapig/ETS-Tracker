"""Fetch current KTMB vehicle positions."""
from google.transit import gtfs_realtime_pb2
import httpx

r = httpx.get(
    "https://api.data.gov.my/gtfs-realtime/vehicle-position/ktmb/",
    headers={"User-Agent": "ETS-Live-Malaysia/1.0"},
    follow_redirects=True,
    timeout=30,
)
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(r.content)
print(f"Entities: {len(feed.entity)}")
for e in feed.entity[:30]:
    if not e.HasField("vehicle"):
        continue
    vp = e.vehicle
    trip_id = vp.trip.trip_id if vp.HasField("trip") else None
    label = vp.vehicle.label if vp.HasField("vehicle") else None
    route = vp.trip.route_id if vp.HasField("trip") else None
    lat = vp.position.latitude if vp.HasField("position") else None
    print(f"  trip={trip_id} route={route} label={label} lat={lat}")
