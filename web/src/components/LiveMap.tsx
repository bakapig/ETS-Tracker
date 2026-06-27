"use client";

import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import type { Station, Vehicle } from "@/lib/api";
import {
  VEHICLE_CATEGORIES,
  type VehicleCategory,
  getVehicles,
  groupVehiclesByRoute,
  trainIconPath,
} from "@/lib/api";
import {
  MALAYSIA_BOUNDS,
  MALAYSIA_CENTER,
  MAP_DEFAULT_ZOOM,
  MAP_MAX_ZOOM,
  MAP_MIN_ZOOM,
  MAP_STATION_ZOOM,
} from "@/lib/map_bounds";
import "leaflet/dist/leaflet.css";

const TRAIN_CLASSES = [
  "ets",
  "komuter_83",
  "komuter_92",
  "dmu_61",
  "intercity",
  "default",
] as const;

function makeTrainIcon(assetPath: string) {
  return L.divIcon({
    className: "",
    html: `<img src="${assetPath}" width="32" height="32" alt="" style="display:block;filter:drop-shadow(0 2px 4px rgba(0,0,0,.35))" />`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

const trainIcons = Object.fromEntries(
  TRAIN_CLASSES.map((key) => [key, makeTrainIcon(trainIconPath(key))]),
) as Record<string, L.DivIcon>;

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], MAP_STATION_ZOOM);
  }, [lat, lon, map]);
  return null;
}

function FitMalaysiaBounds() {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(L.latLngBounds(MALAYSIA_BOUNDS), { maxZoom: MAP_DEFAULT_ZOOM });
  }, [map]);
  return null;
}

function formatSpeed(speed: number | null): string {
  if (speed == null) return "—";
  return `${speed.toFixed(1)} km/h`;
}

function routeLabel(v: Vehicle): string {
  return (
    v.route_display_name ??
    v.route_short_name ??
    VEHICLE_CATEGORIES[(v.route_category ?? "other") as VehicleCategory]?.label ??
    "—"
  );
}

interface Props {
  station: Station | null;
}

export default function LiveMap({ station }: Props) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [hiddenRoutes, setHiddenRoutes] = useState<Set<string>>(new Set());
  const center = station
    ? ([station.stop_lat, station.stop_lon] as [number, number])
    : MALAYSIA_CENTER;

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getVehicles();
        if (active) setVehicles(data);
      } catch {
        if (active) setVehicles([]);
      }
    };
    load();
    const id = setInterval(load, 30000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  const routeGroups = useMemo(() => groupVehiclesByRoute(vehicles), [vehicles]);

  const visibleVehicles = useMemo(
    () =>
      vehicles.filter((v) => !hiddenRoutes.has(v.route_id ?? "unknown")),
    [vehicles, hiddenRoutes],
  );

  const toggleRoute = (routeId: string) => {
    setHiddenRoutes((prev) => {
      const next = new Set(prev);
      if (next.has(routeId)) next.delete(routeId);
      else next.add(routeId);
      return next;
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {routeGroups.map((group) => {
          const meta = VEHICLE_CATEGORIES[group.category];
          const isHidden = hiddenRoutes.has(group.routeId);
          return (
            <button
              key={group.routeId}
              type="button"
              onClick={() => toggleRoute(group.routeId)}
              title={group.label}
              className={`inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition ${
                isHidden
                  ? "border-zinc-200 bg-zinc-50 text-zinc-400 opacity-60 dark:border-zinc-700 dark:bg-zinc-900"
                  : "border-zinc-200 bg-white text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
              }`}
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ background: isHidden ? "#d4d4d8" : meta.color }}
              />
              <span className="truncate">{group.label}</span>
              <span className="shrink-0 text-zinc-400">
                ({group.vehicles.length})
              </span>
            </button>
          );
        })}
      </div>

      <div className="h-72 overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800 sm:h-96">
        <MapContainer
          center={center}
          zoom={station ? MAP_STATION_ZOOM : MAP_DEFAULT_ZOOM}
          minZoom={MAP_MIN_ZOOM}
          maxZoom={MAP_MAX_ZOOM}
          maxBounds={MALAYSIA_BOUNDS}
          maxBoundsViscosity={1.0}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          {!station && <FitMalaysiaBounds />}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {station && (
            <Recenter lat={station.stop_lat} lon={station.stop_lon} />
          )}
          {station && (
            <Marker position={[station.stop_lat, station.stop_lon]}>
              <Popup>{station.stop_name}</Popup>
            </Marker>
          )}
          {visibleVehicles.map((v) => {
            const iconKey = v.train_class ?? "default";
            const icon = trainIcons[iconKey] ?? trainIcons.default;
            return (
              <Marker
                key={v.vehicle_id}
                position={[v.latitude, v.longitude]}
                icon={icon}
              >
                <Popup>
                  <strong>{v.service_number ?? v.trip_id ?? "—"}</strong>
                  <br />
                  {routeLabel(v)}
                  <br />
                  {formatSpeed(v.speed_kmh)}
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      {vehicles.length > 0 && (
        <div className="space-y-3 rounded-xl border border-zinc-200 p-3 dark:border-zinc-800">
          {routeGroups.map((group) => {
            if (hiddenRoutes.has(group.routeId)) return null;
            const meta = VEHICLE_CATEGORIES[group.category];
            return (
              <div key={group.routeId}>
                <h3 className="mb-1.5 flex items-center gap-2 text-sm font-semibold">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: meta.color }}
                  />
                  {group.label}
                </h3>
                <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                  {group.vehicles.map((v) => (
                    <li key={v.vehicle_id} className="flex justify-between gap-2">
                      <span className="font-medium text-zinc-800 dark:text-zinc-200">
                        {v.service_number ?? v.trip_id ?? "—"}
                      </span>
                      <span className="shrink-0 text-zinc-400">
                        {formatSpeed(v.speed_kmh)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
