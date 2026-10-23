import "@fontsource-variable/archivo/wdth.css";
import "@fontsource-variable/shantell-sans/full.css";
import "./globals.css";

import type { Metadata, Viewport } from "next";
import Link from "next/link";

const SITE_URL = process.env.SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Imazinthecomics: find manga and comics by describing the story",
    template: "%s | Imazinthecomics",
  },
  description:
    "Describe a plot, a mood or a character and get matching manga, manhwa, manhua and Western comics, ranked by meaning instead of keywords.",
  applicationName: "Imazinthecomics",
  authors: [{ name: "Suryansh Verma", url: "https://github.com/SlazzInC0de" }],
  openGraph: { type: "website", siteName: "Imazinthecomics" },
  twitter: { card: "summary_large_image" },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = { themeColor: "#fcfcfa" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="visually-hidden" href="#main">
          Skip to content
        </a>
        <header className="page masthead">
          <Link href="/" className="logo">
            Imazinthecomics
          </Link>
          <nav aria-label="Main">
            <Link href="/search">Browse</Link>
            <Link href="/about">How it works</Link>
            <a href="https://github.com/SlazzInC0de/imazinthecomicz">GitHub</a>
          </nav>
        </header>
        <main id="main" className="page">
          {children}
        </main>
        <footer className="page footer">
          <p>
            Titles, synopses and covers come from{" "}
            <a href="https://anilist.co" rel="noopener">
              AniList
            </a>{" "}
            and{" "}
            <a href="https://comicvine.gamespot.com" rel="noopener">
              Comic Vine
            </a>
            . Covers belong to their publishers. A student project by Suryansh Verma.
          </p>
          <p>
            <a href="https://github.com/SlazzInC0de/imazinthecomicz">Source code</a>
          </p>
        </footer>
      </body>
    </html>
  );
}
