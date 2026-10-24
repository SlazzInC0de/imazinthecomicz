import type { Metadata } from "next";
import "@fontsource/bangers/400.css";
import "@fontsource/comic-neue/400.css";
import "@fontsource/comic-neue/700.css";
import "./globals.css";
import Nav from "@/components/Nav";
import PeelTransition from "@/components/PeelTransition";

export const metadata: Metadata = {
  title: { default: "IMAZINTHECOMICS", template: "%s · IMAZINTHECOMICS" },
  description: "Describe the story you want and find manga, manhwa, Marvel, DC and Western comics that match it.",
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* Splits a cover into red / green / blue plates and offsets them, like a misaligned print run. */}
        <svg width="0" height="0" className="defs" aria-hidden="true">
          <filter id="misreg" x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
            <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
            <feOffset in="r" dx="5" dy="3" result="r2" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
            <feOffset in="b" dx="-5" dy="-2" result="b2" />
            <feBlend in="r2" in2="g" mode="screen" result="rg" />
            <feBlend in="rg" in2="b2" mode="screen" />
          </filter>
        </svg>
        <a href="#main" className="skip">
          Skip to content
        </a>
        <PeelTransition>
          <Nav />
          <main id="main">{children}</main>
          <footer className="footer">
            Data from <a href="https://anilist.co">AniList</a>, <a href="https://metron.cloud">Metron</a> and{" "}
            <a href="https://en.wikipedia.org">Wikipedia</a>. Covers belong to their publishers. © {new Date().getFullYear()} Suryansh Verma
          </footer>
        </PeelTransition>
      </body>
    </html>
  );
}
