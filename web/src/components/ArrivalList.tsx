import type { Arrival } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  on_time: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  delayed: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  early: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300",
  live: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  scheduled: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
};

function statusLabel(status: string, delay: number | null): string {
  if (status === "delayed" && delay != null) return `Delayed ${delay} min`;
  if (status === "early" && delay != null) return `${Math.abs(delay)} min early`;
  if (status === "live") return "Live tracking";
  if (status === "on_time") return "On time";
  return "Scheduled";
}

function dayLabel(serviceDate: string | null): string | null {
  if (!serviceDate) return null;
  const d = new Date(`${serviceDate}T12:00:00`);
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (d.toDateString() === tomorrow.toDateString()) return "Tomorrow";
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

export default function ArrivalList({ arrivals }: { arrivals: Arrival[] }) {
  if (arrivals.length === 0) {
    return (
      <p className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
        No upcoming trains at this station in the next few days.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-zinc-200 overflow-hidden rounded-xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
      {arrivals.map((a) => {
        const day = dayLabel(a.service_date);
        return (
        <li
          key={`${a.trip_id}-${a.service_date ?? "today"}-${a.scheduled_arrival}`}
          className="flex items-center justify-between gap-3 bg-white px-4 py-3 dark:bg-zinc-950"
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-blue-700 dark:text-blue-400">
                {a.service_number ?? a.trip_id}
              </span>
              {a.is_live && (
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-red-500" />
              )}
            </div>
            <p className="truncate text-sm text-zinc-600 dark:text-zinc-400">
              → {a.destination}
            </p>
            {a.is_live && (
              <p className="text-xs text-amber-600 dark:text-amber-400">Live on map</p>
            )}
          </div>
          <div className="text-right">
            {day && (
              <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                {day}
              </p>
            )}
            <p className="text-2xl font-bold tabular-nums">
              {a.estimated_arrival ?? a.scheduled_arrival}
            </p>
            {a.estimated_arrival && (
              <p className="text-xs text-zinc-400 line-through">
                {a.scheduled_arrival}
              </p>
            )}
            <span
              className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[a.status] ?? STATUS_STYLES.scheduled}`}
            >
              {statusLabel(a.status, a.delay_minutes)}
            </span>
          </div>
        </li>
        );
      })}
    </ul>
  );
}
