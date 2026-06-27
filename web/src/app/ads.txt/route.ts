import {
  getAdSenseClientId,
  publisherIdForAdsTxt,
} from "@/lib/adsense";

export function GET() {
  const clientId = getAdSenseClientId();
  if (!clientId) {
    return new Response("# AdSense not configured\n", {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const pubId = publisherIdForAdsTxt(clientId);
  const body = `google.com, ${pubId}, DIRECT, f08c47fec0942fa0\n`;

  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
