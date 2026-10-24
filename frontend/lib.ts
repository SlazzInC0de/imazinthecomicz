export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Comic = {
  id: string;
  source: "anilist" | "metron";
  kind: string;
  title: string;
  alt_title: string | null;
  description: string;
  genres: string[];
  tags: string[];
  publisher: string | null;
  creators: string[];
  year: number | null;
  status: string | null;
  country: string;
  score: number | null;
  volumes: number | null;
  chapters: number | null;
  cover: string | null;
  color: string | null;
  url: string | null;
  tone: number;
  scope: number;
  match?: number;
};

export async function api<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

/**
 * Fandom wiki link. Marvel and DC go to their dedicated wikis, where series
 * pages are named "<Title> Vol <n>". Everything else uses Fandom's cross-wiki
 * search, which surfaces the series' own wiki (e.g. onepiece.fandom.com).
 */
export function fandomUrl(c: Pick<Comic, "title" | "kind" | "volumes">): string {
  const wiki = c.kind === "Marvel" ? "marvel" : c.kind === "DC" ? "dc" : null;
  if (wiki) {
    const query = c.volumes ? `${c.title} Vol ${c.volumes}` : c.title;
    return `https://${wiki}.fandom.com/wiki/Special:Search?query=${encodeURIComponent(query)}`;
  }
  return `https://community.fandom.com/wiki/Special:Search?query=${encodeURIComponent(c.title)}&scope=cross-wiki`;
}

export const KINDS = ["all", "Manga", "Manhwa", "Manhua", "Marvel", "DC", "Western"] as const;
