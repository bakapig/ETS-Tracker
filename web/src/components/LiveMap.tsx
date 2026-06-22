"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import type { Station, Vehicle } from "@/lib/api";
import { getVehicles } from "@/lib/api";
import "leaflet/dist/leaflet.css";

const trainIcon = L.divIcon({
  className: "",
  html: `<div style="background:#2563eb;color:white;border-radius:9999px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)">🚆</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], map.getZoom());
  }, [lat, lon, map]);
  return null;
}

interface Props {
  station: Station | null;
}

export default function LiveMap({ station }: Props) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const center = station
    ? ([station.stop_lat, station.stop_lon] as [number, number])
    : ([4.5, 101.0] as [number, number]);

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

  return (
    <div className="h-72 overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800 sm:h-96">
      <MapContainer
        center={center}
        zoom={station ? 10 : 7}
        scrollWheelZoom={false}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {station && <Recenter lat={station.stop_lat} lon={station.stop_lon} />}
        {station && (
          <Marker position={[station.stop_lat, station.stop_lon]}>
            <Popup>{station.stop_name}</Popup>
          </Marker>
        )}
        {vehicles.map((v) => (
          <Marker
            key={v.vehicle_id}
            position={[v.latitude, v.longitude]}
            icon={trainIcon}
          >
            <Popup>
              <strong>{v.label ?? v.vehicle_id}</strong>
              <br />
              Trip: {v.trip_id ?? "—"}
              <br />
              {v.speed_kmh != null ? `${Math.round(v.speed_kmh)} km/h` : ""}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
