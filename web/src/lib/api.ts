export const VEHICLE_CATEGORIES = {
  ets: { label: "ETS", color: "#2563eb" },
  komuter: { label: "KTM Komuter", color: "#16a34a" },
  intercity: { label: "Intercity", color: "#d97706" },
  shuttle: { label: "Intercity Shuttle", color: "#7c3aed" },
  other: { label: "Other", color: "#71717a" },
} as const;

export type VehicleCategory = keyof typeof VEHICLE_CATEGORIES;

export const CATEGORY_ORDER: VehicleCategory[] = [
  "ets",
  "komuter",
  "intercity",
  "shuttle",
  "other",
];

export interface Station {
  stop_id: string;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
}

export interface Arrival {
  trip_id: string;
  service_number: string | null;
  route_short_name: string;
  route_long_name: string;
  destination: string;
  scheduled_arrival: string;
  scheduled_departure: string;
  service_date: string | null;
  estimated_arrival: string | null;
  delay_minutes: number | null;
  status: string;
  is_live: boolean;
  vehicle_label: string | null;
}

export interface Vehicle {
  vehicle_id: string;
  trip_id: string | null;
  service_number: string | null;
  route_id: string | null;
  route_category: VehicleCategory | null;
  route_short_name: string | null;
  route_long_name: string | null;
  route_display_name: string | null;
  train_class: string | null;
  train_class_label: string | null;
  label: string | null;
  latitude: number;
  longitude: number;
  bearing: number | null;
  speed_kmh: number | null;
  timestamp: number | null;
  occupancy_status: string | null;
}

export const TRAIN_ICON_ASSETS: Record<string, string> = {
  ets: "/trains/ets.svg",
  komuter_83: "/trains/komuter_83.svg",
  komuter_92: "/trains/komuter_92.svg",
  dmu_61: "/trains/dmu_61.svg",
  intercity: "/trains/intercity.svg",
  default: "/trains/default.svg",
};

export function trainIconPath(trainClass: string | null): string {
  if (trainClass && trainClass in TRAIN_ICON_ASSETS) {
    return TRAIN_ICON_ASSETS[trainClass];
  }
  return TRAIN_ICON_ASSETS.default;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function apiHeaders(): HeadersInit {
  if (!API_KEY) return {};
  return { "X-API-Key": API_KEY };
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: apiHeaders(),
    next: { revalidate: 0 },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export function searchStations(query: string): Promise<Station[]> {
  const params = new URLSearchParams({ q: query, ets_only: "false" });
  return fetchJson<Station[]>(`/api/stations?${params}`);
}

export function getArrivals(stopId: string, limit = 10): Promise<Arrival[]> {
  return fetchJson<Arrival[]>(`/api/stations/${stopId}/arrivals?limit=${limit}`);
}

export function getVehicles(): Promise<Vehicle[]> {
  return fetchJson<Vehicle[]>("/api/vehicles");
}

export function getStation(stopId: string): Promise<Station> {
  return fetchJson<Station>(`/api/stations/${stopId}`);
}

export interface RouteGroup {
  routeId: string;
  label: string;
  category: VehicleCategory;
  vehicles: Vehicle[];
}

const ROUTE_SORT: Record<string, number> = {
  ETS: 0,
  "100_47300": 10,
  "100_9000": 11,
  KA15_KD19: 12,
  KC05_KB18: 13,
  ERT: 20,
  ES: 21,
  SH: 30,
  ST: 31,
};

export function groupVehiclesByRoute(vehicles: Vehicle[]): RouteGroup[] {
  const byRoute = new Map<string, Vehicle[]>();
  for (const v of vehicles) {
    const id = v.route_id ?? "unknown";
    const list = byRoute.get(id) ?? [];
    list.push(v);
    byRoute.set(id, list);
  }

  const groups: RouteGroup[] = [];
  for (const [routeId, list] of byRoute) {
    const sample = list[0];
    const category = (sample.route_category ?? "other") as VehicleCategory;
    const label =
      sample.route_display_name ??
      sample.route_short_name ??
      VEHICLE_CATEGORIES[category]?.label ??
      routeId;
    groups.push({ routeId, label, category, vehicles: list });
  }

  groups.sort((a, b) => {
    const ao = ROUTE_SORT[a.routeId] ?? 99;
    const bo = ROUTE_SORT[b.routeId] ?? 99;
    if (ao !== bo) return ao - bo;
    return a.label.localeCompare(b.label);
  });
  return groups;
}

/** @deprecated use groupVehiclesByRoute */
export function groupVehiclesByCategory(
  vehicles: Vehicle[],
): Map<VehicleCategory, Vehicle[]> {
  const groups = new Map<VehicleCategory, Vehicle[]>();
  for (const key of CATEGORY_ORDER) {
    groups.set(key, []);
  }
  for (const v of vehicles) {
    const cat = v.route_category ?? "other";
    const list = groups.get(cat as VehicleCategory) ?? groups.get("other")!;
    list.push(v);
  }
  return groups;
}
