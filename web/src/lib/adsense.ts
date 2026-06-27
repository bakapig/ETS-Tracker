const CLIENT_ID = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID?.trim() ?? "";

const SLOT_ENV: Record<string, string | undefined> = {
  "top-banner": process.env.NEXT_PUBLIC_ADSENSE_SLOT_TOP,
  "bottom-banner": process.env.NEXT_PUBLIC_ADSENSE_SLOT_BOTTOM,
};

export function getAdSenseClientId(): string {
  return CLIENT_ID;
}

export function isAdSenseEnabled(): boolean {
  return CLIENT_ID.length > 0;
}

export function getAdSlotId(slot: string): string | undefined {
  const id = SLOT_ENV[slot]?.trim();
  return id && id.length > 0 ? id : undefined;
}

export function isAdUnitConfigured(slot: string): boolean {
  return isAdSenseEnabled() && !!getAdSlotId(slot);
}

/** `ca-pub-…` → `pub-…` for ads.txt */
export function publisherIdForAdsTxt(clientId: string): string {
  if (clientId.startsWith("ca-pub-")) return clientId.slice(3);
  if (clientId.startsWith("pub-")) return clientId;
  return `pub-${clientId}`;
}
