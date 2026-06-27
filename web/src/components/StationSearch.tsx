"use client";

import { useCallback, useEffect, useState } from "react";
import type { Station } from "@/lib/api";
import { searchStations } from "@/lib/api";

const POPULAR: { label: string; query: string }[] = [
  { label: "KL Sentral", query: "kl sentral" },
  { label: "Kuala Lumpur", query: "kuala lumpur" },
  { label: "Ipoh", query: "ipoh" },
  { label: "Butterworth", query: "butterworth" },
  { label: "Padang Besar", query: "padang besar" },
  { label: "Gemas", query: "gemas" },
];

interface Props {
  onSelect: (station: Station) => void;
  selectedId?: string;
}

export default function StationSearch({ onSelect, selectedId }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Station[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const runSearch = useCallback(async (q: string) => {
    setLoading(true);
    try {
      const data = await searchStations(q);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => runSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query, open, runSearch]);

  const pick = (station: Station) => {
    onSelect(station);
    setQuery(station.stop_name);
    setOpen(false);
  };

  return (
    <div className="relative w-full">
      <label htmlFor="station-search" className="sr-only">
        Search KTMB station
      </label>
      <input
        id="station-search"
        type="search"
        placeholder="Search station (e.g. KL Sentral, Ipoh…)"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        className="w-full rounded-xl border border-zinc-300 bg-white px-4 py-3 text-base shadow-sm outline-none ring-blue-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900"
      />

      <div className="mt-2 flex flex-wrap gap-2">
        {POPULAR.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={async () => {
              setQuery(p.label);
              setOpen(true);
              const data = await searchStations(p.query);
              if (data[0]) pick(data[0]);
            }}
            className="rounded-full border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            {p.label}
          </button>
        ))}
      </div>

      {open && (query.length > 0 || results.length > 0) && (
        <ul className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-xl border border-zinc-200 bg-white shadow-lg dark:border-zinc-700 dark:bg-zinc-900">
          {loading && (
            <li className="px-4 py-3 text-sm text-zinc-400">Searching…</li>
          )}
          {!loading && results.length === 0 && (
            <li className="px-4 py-3 text-sm text-zinc-400">No stations found</li>
          )}
          {results.map((s) => (
            <li key={s.stop_id}>
              <button
                type="button"
                onClick={() => pick(s)}
                className={`w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 ${
                  selectedId === s.stop_id ? "bg-blue-50 dark:bg-blue-950/30" : ""
                }`}
              >
                <span className="font-medium">{s.stop_name}</span>
                <span className="ml-2 text-xs text-zinc-400">#{s.stop_id}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
