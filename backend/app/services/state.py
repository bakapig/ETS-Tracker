from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.gtfs.loader import (
    GtfsDataset,
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
    def ets_trip_ids(self) -> set[str]:
        if not self.dataset:
            return set()
        return {
            trip_id
            for trip_id, trip in self.dataset.trips.items()
            if trip.route_id == "ETS"
        }

    async def load_static(self, force_download: bool = False) -> None:
        data: bytes | None = None
        if not force_download:
            data = load_gtfs_cache()
        if data is None or force_download:
            data = await download_gtfs_static()
            save_gtfs_cache(data)
        self.dataset = load_gtfs_from_zip_bytes(data)
        self.last_static_fetch = datetime.now(MYT)

    async def _realtime_loop(self) -> None:
        while True:
            await fetch_vehicle_positions()
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
