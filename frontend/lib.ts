// 127.0.0.1, not localhost: Node resolves localhost to IPv6 (::1) first, and uvicorn listens on IPv4 only.
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
// Server components can use a private URL (e.g. inside Docker); falls back to the public one.
const SERVER_API = process.env.API_URL ?? API;

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
  wiki_url?: string | null;
  tone: number;
  scope: number;
  match?: number;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = typeof window === "undefined" ? SERVER_API : API;
  const res = await fetch(`${base}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json();
}

/** Returns null instead of throwing, for decorative sections that should simply hide when the API is down. */
export async function tryApi<T>(path: string): Promise<T | null> {
  try {
    return await api<T>(path);
  } catch {
    return null;
  }
}

export const KINDS = ["all", "Manga", "Manhwa", "Manhua", "Marvel", "DC", "Western"] as const;
export type Kind = (typeof KINDS)[number];

export function fandomUrl(c: Pick<Comic, "title" | "kind" | "volumes">): string {
  const wiki = c.kind === "Marvel" ? "marvel" : c.kind === "DC" ? "dc" : null;
  if (wiki) {
    const query = c.volumes ? `${c.title} Vol ${c.volumes}` : c.title;
    return `https://${wiki}.fandom.com/wiki/Special:Search?query=${encodeURIComponent(query)}`;
  }
  return `https://community.fandom.com/wiki/Special:Search?query=${encodeURIComponent(c.title)}&scope=cross-wiki`;
}

/** One short line under a title: year, then publisher or AniList score. Each value says what it is. */
export function metaLine(c: Comic): string {
  return [c.year, c.publisher, c.score ? `★ ${c.score} on AniList` : null].filter(Boolean).join(" · ");
}

export function shortText(text: string, max = 170): string {
  if (text.length <= max) return text;
  const cut = text.slice(0, max);
  return cut.slice(0, cut.lastIndexOf(" ")) + "...";
}
