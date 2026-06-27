from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.gtfs.categories import enrich_vehicle
from app.gtfs.loader import (
    GtfsDataset,
    calendar_stale,
    download_gtfs_static,
    load_gtfs_cache,
    load_gtfs_from_zip_bytes,
    save_gtfs_cache,
)
from app.gtfs.realtime import fetch_vehicle_positions, realtime_store

MYT = ZoneInfo("Asia/Kuala_Lumpur")


class AppState:
    def __init__(self) -> None:
        self.dataset: GtfsDataset | None = None
        self.last_static_fetch: datetime | None = None
        self._realtime_task: asyncio.Task | None = None
        self._static_task: asyncio.Task | None = None

    @property
    def ets_trip_ids(self) -> frozenset[str]:
        if not self.dataset:
            return frozenset()
        return self.dataset.ets_trip_ids

    def refresh_enriched_vehicles(self) -> None:
        dataset = self.dataset
        realtime_store.enriched_vehicles = [
            enrich_vehicle(v, dataset) for v in realtime_store.vehicles
        ]

    async def load_static(self, force_download: bool = False) -> None:
        data: bytes | None = None
        if not force_download:
            data = await asyncio.to_thread(load_gtfs_cache)
            if data is not None:
                preview = await asyncio.to_thread(load_gtfs_from_zip_bytes, data)
                if calendar_stale(preview):
                    data = None

        if data is None or force_download:
            data = await download_gtfs_static()
            await asyncio.to_thread(save_gtfs_cache, data)

        self.dataset = await asyncio.to_thread(load_gtfs_from_zip_bytes, data)
        self.last_static_fetch = datetime.now(MYT)
        from app.gtfs.trip_numbers import reload_trip_lookup

        reload_trip_lookup()
        self.refresh_enriched_vehicles()

    async def _realtime_loop(self) -> None:
        while True:
            await fetch_vehicle_positions()
            self.refresh_enriched_vehicles()
            await asyncio.sleep(settings.realtime_poll_seconds)

    async def _static_refresh_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.gtfs_refresh_hours * 3600)
            try:
                await self.load_static(force_download=True)
            except Exception:  # noqa: BLE001
                pass

    async def start_background_tasks(self) -> None:
        await fetch_vehicle_positions()
        self.refresh_enriched_vehicles()
        self._realtime_task = asyncio.create_task(self._realtime_loop())
        self._static_task = asyncio.create_task(self._static_refresh_loop())

    async def stop_background_tasks(self) -> None:
        for task in (self._realtime_task, self._static_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


app_state = AppState()
