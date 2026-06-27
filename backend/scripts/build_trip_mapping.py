"""Build trip_id -> public service number mapping from GTFS + official ETS PDF."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
import runpy
from pathlib import Path

import httpx

_PARSER = runpy.run_path(str(Path(__file__).resolve().parent / "parse_ets_pdf.py"))
parse_ets_pdf = _PARSER["parse_ets_pdf"]
PDF_JSON = _PARSER["OUTPUT_JSON"]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GTFS_ZIP = DATA_DIR / "ktmb_gtfs.zip"
OUTPUT = DATA_DIR / "trip_service_numbers.json"

# GTFS trip_id -> service number when auto-match is ambiguous (Jun 2026 PDF).
TRIP_ID_OVERRIDES: dict[str, str] = {
    "9171": "EP9123",  # Butterworth 06:10 -> KL (PDF: dep 07:50 arr KL 10:35)
    "9173": "EP9123",  # Butterworth 10:00 -> KL (same service, GTFS time drift)
    "9176": "EP9136",  # KL 14:45 -> Butterworth (PDF KL dep 15:55)
    "9178": "EP9138",  # KL 19:55 -> Butterworth (PDF KL dep 20:15)
    "9273": "EP9123",  # Padang Besar 11:05 -> KL (PDF PB dep 12:05)
}


def _norm_stop(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().upper())


def _time_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _load_gtfs() -> tuple[list[dict], dict[str, str], list[dict]]:
    if not GTFS_ZIP.exists():
        r = httpx.get(
            "https://api.data.gov.my/gtfs-static/ktmb/",
            headers={"User-Agent": "ETS-Live-Malaysia/1.0"},
            follow_redirects=True,
            timeout=120,
        )
        r.raise_for_status()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        GTFS_ZIP.write_bytes(r.content)

    with zipfile.ZipFile(GTFS_ZIP) as zf:
        names = {n.lower().split("/")[-1]: n for n in zf.namelist()}
        trips = list(csv.DictReader(io.StringIO(zf.read(names["trips.txt"]).decode("utf-8-sig"))))
        stops = {
            s["stop_id"]: _norm_stop(s["stop_name"])
            for s in csv.DictReader(io.StringIO(zf.read(names["stops.txt"]).decode("utf-8-sig")))
        }
        stop_times = list(
            csv.DictReader(io.StringIO(zf.read(names["stop_times.txt"]).decode("utf-8-sig")))
        )
    return trips, stops, stop_times


def _load_pdf_data() -> dict:
    if not PDF_JSON.exists():
        return parse_ets_pdf()
    return json.loads(PDF_JSON.read_text(encoding="utf-8"))


def _match_nb_kl(
    departure: str,
    destination: str,
    pdf: dict,
    max_delta: int = 30,
) -> tuple[str | None, str]:
    nb = pdf.get("northbound", {})
    dep_m = _time_minutes(departure)

    exact = [
        svc
        for svc, meta in nb.items()
        if meta.get("kl_sentral_departure") == departure
    ]
    if len(exact) == 1:
        return exact[0], "pdf_kl_exact"
    if len(exact) > 1:
        return exact[0], "pdf_kl_exact_multi"

    best_svc = None
    best_delta = max_delta + 1
    for svc, meta in nb.items():
        kl_dep = meta.get("kl_sentral_departure")
        if not kl_dep:
            continue
        delta = abs(_time_minutes(kl_dep) - dep_m)
        if delta <= max_delta and delta < best_delta:
            best_svc = svc
            best_delta = delta
    if best_svc:
        return best_svc, "pdf_kl_fuzzy"
    return None, "unmatched"


def _match_sb_terminal(
    origin: str,
    departure: str,
    pdf: dict,
    max_delta: int = 90,
) -> tuple[str | None, str]:
    terminals = pdf.get("southbound", {}).get("terminal_departures", {})
    dep_m = _time_minutes(departure)

    best_svc = None
    best_delta = max_delta + 1
    for key, svc in terminals.items():
        station, dep = key.split("|", 1)
        if station != origin:
            continue
        delta = abs(_time_minutes(dep) - dep_m)
        if delta <= max_delta and delta < best_delta:
            best_svc = svc
            best_delta = delta
    if best_svc:
        return best_svc, "pdf_terminal_fuzzy"
    return None, "unmatched"


def resolve_ets_service(
    trip_id: str,
    origin: str,
    destination: str,
    departure: str,
    pdf: dict,
) -> tuple[str, str]:
    if trip_id in TRIP_ID_OVERRIDES:
        return TRIP_ID_OVERRIDES[trip_id], "pdf_override"

    if origin == "KL SENTRAL":
        svc, how = _match_nb_kl(departure, destination, pdf)
        if svc:
            return svc, how

    if destination == "KL SENTRAL":
        svc, how = _match_sb_terminal(origin, departure, pdf)
        if svc:
            return svc, how

    if trip_id.isdigit():
        return f"EG{trip_id}", "fallback_eg"
    return trip_id, "fallback_raw"


def build_mapping() -> dict[str, dict]:
    trips, stops, stop_times = _load_gtfs()
    pdf = _load_pdf_data()
    mapping: dict[str, dict] = {}

    for trip in trips:
        tid = trip["trip_id"]
        route_id = trip["route_id"]
        sts = sorted(
            [st for st in stop_times if st["trip_id"] == tid],
            key=lambda x: int(x["stop_sequence"]),
        )
        if not sts:
            continue

        origin = stops[sts[0]["stop_id"]]
        dest = stops[sts[-1]["stop_id"]]
        dep = sts[0]["departure_time"][:5]

        entry: dict = {
            "route_id": route_id,
            "origin": origin,
            "destination": dest,
            "departure": dep,
        }

        if route_id == "ETS":
            service, match_type = resolve_ets_service(tid, origin, dest, dep, pdf)
            entry["service_number"] = service
            entry["match_type"] = match_type
            if match_type in ("fallback_eg", "fallback_raw", "unmatched"):
                entry["unverified"] = True
        else:
            entry["service_number"] = tid
            entry["match_type"] = "gtfs_trip_id"

        mapping[tid] = entry

    return mapping


def main() -> None:
    if not PDF_JSON.exists():
        data = parse_ets_pdf()
        PDF_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    mapping = build_mapping()
    OUTPUT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    ets = {k: v for k, v in mapping.items() if v["route_id"] == "ETS"}
    verified = sum(1 for v in ets.values() if not v.get("unverified"))
    print(f"Wrote {len(mapping)} trips to {OUTPUT}")
    print(f"ETS: {len(ets)} total, {verified} verified")
    for tid, v in sorted(ets.items()):
        flag = "" if not v.get("unverified") else " ?"
        print(
            f"  {tid} -> {v['service_number']}{flag}  "
            f"({v.get('match_type')}) {v['departure']} {v['origin']} -> {v['destination']}"
        )


if __name__ == "__main__":
    main()
