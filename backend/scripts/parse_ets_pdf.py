"""Parse KTMB ETS timetable PDF (Jun 2026) — reliable KL Sentral columns."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

SOURCE_PDF = (
    Path(__file__).resolve().parent.parent.parent
    / "source"
    / "Jadual Tren ETS 1 Jun 2026.pdf"
)
OUTPUT_JSON = Path(__file__).resolve().parent.parent / "data" / "ets_pdf_services.json"

SERVICE_RE = re.compile(r"(EG|EP|EX|ES)(\d{4})")


def _parse_services(header_line: str) -> list[str]:
    return [f"{a}{b}" for a, b in SERVICE_RE.findall(header_line)]


def _extract_table_text(page) -> str | None:
    for table in page.extract_tables() or []:
        for row in table:
            for cell in row:
                if cell and "STESEN/STATION" in cell and SERVICE_RE.search(cell):
                    return cell
    return None


def _station_times_from_tokens(rest: str, n_services: int) -> list[str | None]:
    tokens = rest.split()
    times: list[str | None] = []
    for tok in tokens:
        if tok == "-":
            times.append(None)
        elif re.fullmatch(r"\d{1,2}:\d{2}", tok):
            times.append(tok)
        else:
            times.append(None)
    if len(times) < n_services:
        times.extend([None] * (n_services - len(times)))
    return times[:n_services]


def _parse_page(text: str) -> tuple[list[str], dict[str, list[str | None]]]:
    lines = text.split("\n")
    header = next(l for l in lines if "STESEN/STATION" in l)
    services = _parse_services(header)
    stations: dict[str, list[str | None]] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("STESEN/"):
            continue
        if any(x in stripped.upper() for x in ("PETUNUK", "LEGEND", "PERKHIDMATAN", "SERVICES")):
            continue
        m = re.match(r"^([A-Z][A-Z0-9 /.'()-]+?)\s+((?:\d{1,2}:\d{2}|\-|\s)+)$", stripped)
        if not m:
            continue
        name = m.group(1).strip().upper()
        if name in {"22", "PERKHIDMATAN", "SERVICES"}:
            continue
        stations[name] = _station_times_from_tokens(m.group(2), len(services))
    return services, stations


def parse_ets_pdf(pdf_path: Path = SOURCE_PDF) -> dict:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    result: dict = {
        "source": pdf_path.name,
        "effective": "2026-06-01",
        "northbound": {},
        "southbound": {},
    }

    with pdfplumber.open(pdf_path) as doc:
        nb_text = _extract_table_text(doc.pages[0])
        sb_text = _extract_table_text(doc.pages[1])
        if not nb_text or not sb_text:
            raise ValueError("Could not extract ETS timetable tables")

        nb_services, nb_stations = _parse_page(nb_text)
        sb_services, sb_stations = _parse_page(sb_text)

        for svc, dep in zip(nb_services, nb_stations.get("KL SENTRAL", [])):
            if dep:
                result["northbound"][svc] = {
                    "kl_sentral_departure": dep,
                    "direction": "northbound",
                }

        for svc, arr in zip(sb_services, sb_stations.get("KL SENTRAL", [])):
            if arr:
                result["southbound"][svc] = {
                    "kl_sentral_arrival": arr,
                    "direction": "southbound",
                }

        # Terminal departures on southbound page (for trains heading to KL)
        for station in ("IPOH", "BUTTERWORTH", "PADANG BESAR", "JB SENTRAL", "GEMAS"):
            row = sb_stations.get(station)
            if not row:
                continue
            for svc, dep in zip(sb_services, row):
                if dep:
                    key = f"{station}|{dep}"
                    result["southbound"].setdefault(
                        "terminal_departures",
                        {},
                    )[key] = svc

    return result


def main() -> None:
    data = parse_ets_pdf()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")
    print(f"  Northbound KL departures: {len(data['northbound'])}")
    print(f"  Southbound KL arrivals: {len(data['southbound']) - 1}")
    print(f"  EG9052 -> {data['northbound'].get('EG9052')}")


if __name__ == "__main__":
    main()
