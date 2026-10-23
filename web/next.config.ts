import type { NextConfig } from "next";

const dev = process.env.NODE_ENV !== "production";

// Covers are hotlinked from the two data sources; nothing else is loaded from outside.
const csp = [
  "default-src 'self'",
  // Next inlines its hydration data as <script> tags, hence 'unsafe-inline'. No outside scripts.
  `script-src 'self' 'unsafe-inline'${dev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https://s4.anilist.co https://img.anili.st https://comicvine.gamespot.com https://static.metron.cloud https://metron.cloud",
  "font-src 'self'",
  `connect-src 'self'${dev ? " ws:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");

const config: NextConfig = {
  poweredByHeader: false,
  agentRules: false,
  reactStrictMode: true,
  productionBrowserSourceMaps: false,
  images: { unoptimized: true },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        ],
      },
    ];
  },
};

export default config;
