/** AdSense placeholder — replace with real ad unit after approval */
export default function AdBanner({ slot = "banner" }: { slot?: string }) {
  return (
    <div
      className="flex h-20 w-full items-center justify-center rounded-lg border border-dashed border-zinc-300 bg-zinc-50 text-xs text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-500"
      data-ad-slot={slot}
      aria-label="Advertisement placeholder"
    >
      Ad space ({slot}) — connect Google AdSense here
    </div>
  );
}
