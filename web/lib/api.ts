import "server-only";

import { headers } from "next/headers";

const API_URL = (process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const PROXY_KEY = process.env.PROXY_KEY ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function visitorIp(): Promise<string> {
  const h = await headers();
  return (h.get("x-forwarded-for")?.split(",")[0] ?? h.get("x-real-ip") ?? "").trim();
}

type Options = {
  /** Per-visitor request (search): forwards the visitor IP so the API rate limits them, never cached. */
  visitor?: boolean;
  /** Seconds to cache shared responses (comic pages, facets). */
  revalidate?: number;
};

export async function api<T>(path: string, params?: URLSearchParams, opts: Options = {}): Promise<T> {
  const url = `${API_URL}${path}${params && params.size ? `?${params}` : ""}`;
  const h: Record<string, string> = { Accept: "application/json" };
  if (PROXY_KEY) h["X-Proxy-Key"] = PROXY_KEY;
  if (opts.visitor) {
    const ip = await visitorIp();
    if (ip) h["X-Client-IP"] = ip;
  }
  let res: Response;
  try {
    res = await fetch(url, {
      headers: h,
      signal: AbortSignal.timeout(10_000),
      ...(opts.visitor ? { cache: "no-store" as const } : { next: { revalidate: opts.revalidate ?? 300 } }),
    });
  } catch {
    throw new ApiError(503, "The search service did not answer.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}
