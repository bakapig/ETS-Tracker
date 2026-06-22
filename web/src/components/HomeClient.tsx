"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import type { Arrival, Station } from "@/lib/api";
import { getArrivals } from "@/lib/api";
import AdBanner from "./AdBanner";
import ArrivalList from "./ArrivalList";
import StationSearch from "./StationSearch";

const LiveMap = dynamic(() => import("./LiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 text-sm text-zinc-400 dark:border-zinc-800 dark:bg-zinc-900 sm:h-96">
      Loading map…
    </div>
  ),
});

export default function HomeClient() {
  const [station, setStation] = useState<Station | null>(null);
  const [arrivals, setArrivals] = useState<Arrival[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadArrivals = useCallback(async (s: Station) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getArrivals(s.stop_id);
      setArrivals(data);
    } catch {
      setError("Could not load arrivals. Is the backend running on port 8000?");
      setArrivals([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const onSelect = (s: Station) => {
    setStation(s);
    loadArrivals(s);
  };

  useEffect(() => {
    if (!station) return;
    const id = setInterval(() => loadArrivals(station), 30000);
    return () => clearInterval(id);
  }, [station, loadArrivals]);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-6">
      <header className="space-y-1">
        <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
          Malaysia KTMB · Official GTFS
        </p>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          ETS Live Malaysia
        </h1>
        <p className="text-sm text-zinc-500">
          Next ETS arrivals, live train map &amp; delay estimates
        </p>
      </header>

      <StationSearch onSelect={onSelect} selectedId={station?.stop_id} />

      <AdBanner slot="top-banner" />

      {station && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{station.stop_name}</h2>
            <button
              type="button"
              onClick={() => loadArrivals(station)}
              className="text-sm text-blue-600 hover:underline dark:text-blue-400"
            >
              Refresh
            </button>
          </div>

          {loading && (
            <p className="text-sm text-zinc-400">Loading arrivals…</p>
          )}
          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
              {error}
            </p>
          )}
          {!loading && !error && <ArrivalList arrivals={arrivals} />}
        </section>
      )}

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Live ETS map</h2>
        <LiveMap station={station} />
        <p className="text-xs text-zinc-400">
          Positions refresh every 30s from Malaysia Open API
        </p>
      </section>

      <AdBanner slot="bottom-banner" />
    </div>
  );
}
