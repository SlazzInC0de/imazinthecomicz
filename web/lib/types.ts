export type Kind = "Manga" | "Manhwa" | "Manhua" | "Western";

export interface Card {
  id: string;
  title: string;
  kind: Kind;
  format: string;
  year: number | null;
  status: string | null;
  score: number | null;
  genres: string[];
  cover: string | null;
  cover_color: string | null;
  length: number | null;
  length_unit: string;
  publisher: string | null;
  creators: string[];
  source: string;
  blurb: string;
  match?: {
    label: "strong" | "good" | "loose" | null;
    matched: string[];
    semantic: number | null;
    score: number;
  };
  similarity?: number;
}

export interface Comic extends Omit<Card, "blurb" | "match" | "similarity"> {
  alt_titles: string[];
  tags: string[];
  description: string;
  url: string | null;
  popularity: number;
  tone: number;
  scope: number;
}

export interface SearchResponse {
  query: string;
  mode: "hybrid" | "keyword";
  total: number;
  offset: number;
  took_ms: number;
  results: Card[];
}

export interface BrowseResponse {
  total: number;
  offset: number;
  results: Card[];
}

export interface Facets {
  total: number;
  kinds: Record<string, number>;
  genres: Record<string, number>;
  statuses: string[];
  year_min: number | null;
  year_max: number | null;
  mode: "hybrid" | "keyword";
  built_at: string | null;
  model: string | null;
}
