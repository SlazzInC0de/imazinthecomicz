import type { MetadataRoute } from "next";

import { api } from "@/lib/api";

export const revalidate = 86400;

const SITE_URL = (process.env.SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE_URL}/about`, changeFrequency: "monthly", priority: 0.5 },
  ];
  try {
    const { ids } = await api<{ ids: string[] }>("/api/ids", new URLSearchParams({ limit: "20000" }), {
      revalidate: 86400,
    });
    for (const id of ids) pages.push({ url: `${SITE_URL}/comic/${id}`, changeFrequency: "monthly", priority: 0.7 });
  } catch {
    // API down at build time: ship the static pages, the next revalidation adds the rest
  }
  return pages;
}
