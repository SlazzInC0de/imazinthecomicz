import type { MetadataRoute } from "next";

const SITE_URL = (process.env.SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

export default function robots(): MetadataRoute.Robots {
  return {
    // search result pages are noindex but crawlable, so links on them are followed
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
