import { NextResponse, type NextRequest } from "next/server";

/**
 * Per-request Content Security Policy with a fresh nonce. Next reads the nonce
 * from the request's CSP header and puts it on its own scripts, so no inline
 * script runs unless this response created it.
 */
export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const dev = process.env.NODE_ENV === "development";
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    // inline style attributes (cover colours) are harmless; scripts are what the nonce guards
    "style-src 'self' 'unsafe-inline'",
    // covers are hotlinked from the data sources' CDNs
    "img-src 'self' data: https://s4.anilist.co https://img.anili.st https://comicvine.gamespot.com https://static.metron.cloud https://metron.cloud",
    "font-src 'self'",
    `connect-src 'self'${dev ? " ws:" : ""}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests",
  ].join("; ");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    {
      source: "/((?!_next/static|_next/image|icon.svg|llms.txt|robots.txt|sitemap.xml).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
