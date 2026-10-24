import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IMAZINTHECOMICS",
  description: "Describe the story you want. Get manga, manhwa and Western comics that match it.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Bangers&family=Space+Grotesk:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <header className="masthead">
          <a href="/" className="logo">
            IMAZIN<span>THE</span>COMICS
          </a>
          <p className="tagline">semantic search across manga, manhwa &amp; Western comics</p>
        </header>
        <main>{children}</main>
        <footer className="footer">
          Data from <a href="https://anilist.co">AniList</a> and <a href="https://metron.cloud">Metron</a>. ©{" "}
          {new Date().getFullYear()} Suryansh Verma
        </footer>
      </body>
    </html>
  );
}
