"""One-off GTFS inspection script."""
import csv
import io
import zipfile
from collections import Counter
from pathlib import Path

import httpx

path = Path(__file__).resolve().parent.parent / "data" / "ktmb_gtfs.zip"
if not path.exists():
    r = httpx.get(
        "https://api.data.gov.my/gtfs-static/ktmb/",
        headers={"User-Agent": "ETS-Live-Malaysia/1.0"},
        follow_redirects=True,
        timeout=120,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    print("Downloaded", len(r.content), "bytes")

with zipfile.ZipFile(path) as zf:
    names = {n.lower().split("/")[-1]: n for n in zf.namelist()}
    print("Files:", sorted(names.keys()))

    trips = list(csv.DictReader(io.StringIO(zf.read(names["trips.txt"]).decode("utf-8-sig"))))
    routes = list(csv.DictReader(io.StringIO(zf.read(names["routes.txt"]).decode("utf-8-sig"))))
    stops = {s["stop_id"]: s["stop_name"] for s in csv.DictReader(io.StringIO(zf.read(names["stops.txt"]).decode("utf-8-sig")))}
    stop_times = list(csv.DictReader(io.StringIO(zf.read(names["stop_times.txt"]).decode("utf-8-sig"))))

    ets_trips = [t for t in trips if t["route_id"] == "ETS"]
    print(f"Total trips: {len(trips)}, ETS trips: {len(ets_trips)}")
    print("All routes:", [(r["route_id"], r.get("route_short_name", ""), r.get("route_long_name", "")[:60]) for r in routes])

    sample_ids = sorted(set(t["trip_id"] for t in ets_trips))[:20]
    print("Sample ETS trip_ids:", sample_ids)

    t9052 = [t for t in ets_trips if "9052" in t["trip_id"]]
    print("Trips matching 9052:", t9052)

    dirs = Counter(t["direction_id"] for t in ets_trips)
    print("ETS direction_id counts:", dict(dirs))

    # Extract numeric suffix from trip_id if pattern exists
  # realtime uses short id like 9052
    for t in ets_trips[:5]:
        print("trip head:", t["trip_id"][:80])

    if t9052:
        tid = t9052[0]["trip_id"]
        st9052 = sorted([st for st in stop_times if st["trip_id"] == tid], key=lambda x: int(x["stop_sequence"]))
        print(f"Schedule for trip {tid}:")
        for st in st9052:
            name = stops.get(st["stop_id"], st["stop_id"])
            print(f"  {st['stop_sequence']:>2} {name:30} arr={st['arrival_time']} dep={st['departure_time']}")

    print("\nAll ETS services:")
    for t in sorted(ets_trips, key=lambda x: x["trip_id"]):
        tid = t["trip_id"]
        sts = sorted([st for st in stop_times if st["trip_id"] == tid], key=lambda x: int(x["stop_sequence"]))
        if not sts:
            continue
        o = stops[sts[0]["stop_id"]]
        d = stops[sts[-1]["stop_id"]]
        dep = sts[0]["departure_time"]
        print(f"  {tid} dir={t['direction_id']} {o} -> {d} dep {dep}")
