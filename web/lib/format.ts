import type { Card, Comic } from "./types";

/** "Manhwa, 2018" or "Western, Image Comics, 1992" */
export function metaLine(c: Pick<Card, "kind" | "year" | "publisher">): string {
  return [c.kind, c.publisher, c.year].filter(Boolean).join(", ");
}

export function lengthText(c: Pick<Card, "length" | "length_unit">): string | null {
  if (!c.length) return null;
  const unit = c.length === 1 ? c.length_unit.replace(/s$/, "") : c.length_unit;
  return `${c.length.toLocaleString("en-US")} ${unit}`;
}

export function matchText(label: string | null | undefined): string | null {
  if (label === "strong") return "Strong match";
  if (label === "good") return "Good match";
  if (label === "loose") return "Loose match";
  return null;
}

export function sourceName(c: Pick<Comic, "source">): string {
  return c.source === "AniList" ? "AniList" : c.source;
}

/** Short meta description for search engines and link previews. */
export function summary(text: string, max = 158): string {
  const flat = text.replace(/\s+/g, " ").trim();
  if (flat.length <= max) return flat;
  return flat.slice(0, max).replace(/\s+\S*$/, "") + "…";
}
