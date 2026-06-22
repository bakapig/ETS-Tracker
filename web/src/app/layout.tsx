import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ETS Live Malaysia — Real-time KTMB Arrivals",
  description:
    "Track ETS train arrivals, delays and live positions across Malaysia using official KTMB GTFS data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
        {children}
        <footer className="mt-auto border-t border-zinc-200 px-4 py-4 text-center text-xs text-zinc-400 dark:border-zinc-800">
          Data from{" "}
          <a
            href="https://developer.data.gov.my/realtime-api/gtfs-realtime"
            className="underline hover:text-zinc-600"
            target="_blank"
            rel="noreferrer"
          >
            Malaysia Open API (KTMB GTFS)
          </a>
          . Not affiliated with KTMB.
        </footer>
      </body>
    </html>
  );
}
