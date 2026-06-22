const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Station {
  stop_id: string;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
}

export interface Arrival {
  trip_id: string;
  route_short_name: string;
  route_long_name: string;
  destination: string;
  scheduled_arrival: string;
  scheduled_departure: string;
  estimated_arrival: string | null;
  delay_minutes: number | null;
  status: string;
  is_live: boolean;
  vehicle_label: string | null;
}

export interface Vehicle {
  vehicle_id: string;
  trip_id: string | null;
  route_id: string | null;
  label: string | null;
  latitude: number;
  longitude: number;
  bearing: number | null;
  speed_kmh: number | null;
  timestamp: number | null;
  occupancy_status: string | null;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 0 } });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export function searchStations(query: string): Promise<Station[]> {
  const params = new URLSearchParams({ q: query, ets_only: "true" });
  return fetchJson<Station[]>(`/api/stations?${params}`);
}

export function getArrivals(stopId: string, limit = 10): Promise<Arrival[]> {
  return fetchJson<Arrival[]>(`/api/stations/${stopId}/arrivals?limit=${limit}`);
}

export function getVehicles(): Promise<Vehicle[]> {
  return fetchJson<Vehicle[]>("/api/vehicles?ets_only=true");
}

export function getStation(stopId: string): Promise<Station> {
  return fetchJson<Station>(`/api/stations/${stopId}`);
}
