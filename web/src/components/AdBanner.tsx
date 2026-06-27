"use client";

import { useEffect, useRef } from "react";
import {
  getAdSenseClientId,
  getAdSlotId,
  isAdUnitConfigured,
} from "@/lib/adsense";

declare global {
  interface Window {
    adsbygoogle: Record<string, unknown>[];
  }
}

function AdPlaceholder({ slot }: { slot: string }) {
  return (
    <div
      className="flex h-20 w-full items-center justify-center rounded-lg border border-dashed border-zinc-300 bg-zinc-50 text-xs text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-500"
      data-ad-slot={slot}
      aria-label="Advertisement placeholder"
    >
      Ad space ({slot})
    </div>
  );
}

export default function AdBanner({ slot = "banner" }: { slot?: string }) {
  const clientId = getAdSenseClientId();
  const adSlotId = getAdSlotId(slot);
  const enabled = isAdUnitConfigured(slot);
  const pushed = useRef(false);

  useEffect(() => {
    if (!enabled || pushed.current) return;
    pushed.current = true;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // Ad blockers or script not loaded yet — fail silently
    }
  }, [enabled, slot]);

  if (!enabled || !adSlotId) {
    return <AdPlaceholder slot={slot} />;
  }

  return (
    <div className="w-full overflow-hidden" aria-label="Advertisement">
      <ins
        className="adsbygoogle block"
        style={{ display: "block" }}
        data-ad-client={clientId}
        data-ad-slot={adSlotId}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}
