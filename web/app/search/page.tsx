import type { Metadata } from "next";
import Link from "next/link";

import ComicCard from "@/components/ComicCard";
import FilterPanel from "@/components/FilterPanel";
import Filters, { type FilterState } from "@/components/Filters";
import SearchBalloon from "@/components/SearchBalloon";
import { api, ApiError } from "@/lib/api";
import type { BrowseResponse, Facets, SearchResponse } from "@/lib/types";

import styles from "./search.module.css";

const PAGE_SIZE = 24;
const MAX_SEARCH_PAGES = 4; // the API ranks the best 96 matches
const MAX_BROWSE_PAGES = Math.floor(5000 / PAGE_SIZE) + 1; // the API accepts offsets up to 5,000

type Params = Promise<Record<string, string | string[] | undefined>>;

function one(v: string | string[] | undefined): string {
  return (Array.isArray(v) ? v[0] : v ?? "").trim();
}

function many(v: string | string[] | undefined): string[] {
  return (Array.isArray(v) ? v : v ? [v] : []).map((s) => s.trim()).filter(Boolean);
}

function readState(sp: Record<string, string | string[] | undefined>): FilterState & { page: number } {
  // same ranges the API enforces, so a hand-edited URL never turns into a 422
  const num = (s: string, min: number, max: number) =>
    /^\d{1,4}$/.test(s) && Number(s) >= min && Number(s) <= max ? s : "";
  const unit = (s: string) => (/^(0(\.\d+)?|1(\.0+)?)$/.test(s) ? s : "");
  return {
    q: one(sp.q).slice(0, 200),
    kind: many(sp.kind).filter((k) => ["Manga", "Manhwa", "Manhua", "Western"].includes(k)),
    genre: many(sp.genre).slice(0, 6),
    year_min: num(one(sp.year_min), 1900, 2100),
    year_max: num(one(sp.year_max), 1900, 2100),
    status: one(sp.status),
    min_score: num(one(sp.min_score), 0, 100),
    tone: unit(one(sp.tone)),
    scope: unit(one(sp.scope)),
    sort: ["popular", "score", "newest"].includes(one(sp.sort)) ? one(sp.sort) : "",
    page: Math.max(1, Math.min(MAX_BROWSE_PAGES, parseInt(one(sp.page) || "1", 10) || 1)),
  };
}

function toParams(s: ReturnType<typeof readState>, extra: Record<string, string> = {}) {
  const p = new URLSearchParams();
  if (s.q) p.set("q", s.q);
  s.kind.forEach((k) => p.append("kind", k));
  s.genre.forEach((g) => p.append("genre", g));
  for (const key of ["year_min", "year_max", "status", "min_score", "tone", "scope", "sort"] as const) {
    if (s[key]) p.set(key, s[key]);
  }
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p;
}

export async function generateMetadata({ searchParams }: { searchParams: Params }): Promise<Metadata> {
  const s = readState(await searchParams);
  return {
    title: s.q ? `Comics like “${s.q}”` : "Browse manga and comics",
    // result pages are endless combinations; keep them out of search indexes
    robots: { index: false, follow: true },
    alternates: { canonical: "/search" },
  };
}

export default async function SearchPage({ searchParams }: { searchParams: Params }) {
  const state = readState(await searchParams);
  if (state.year_min && state.year_max && Number(state.year_min) > Number(state.year_max)) {
    [state.year_min, state.year_max] = [state.year_max, state.year_min];
  }
  const apiParams = toParams(state);
  apiParams.delete("sort");
  apiParams.set("limit", String(PAGE_SIZE));
  apiParams.set("offset", String((state.page - 1) * PAGE_SIZE));
  if (!state.q) {
    apiParams.delete("tone");
    apiParams.delete("scope");
    apiParams.set("sort", state.sort || "popular");
  }

  let facets: Facets | null = null;
  let data: SearchResponse | BrowseResponse | null = null;
  let error: string | null = null;
  const tooDeep = state.q !== "" && state.page > MAX_SEARCH_PAGES;
  // facets only feed the filter counts; results still load without them
  facets = await api<Facets>("/api/facets", undefined, { revalidate: 3600 }).catch(() => null);
  try {
    if (!tooDeep) {
      data = state.q
        ? await api<SearchResponse>("/api/search", apiParams, { visitor: true })
        : await api<BrowseResponse>("/api/browse", apiParams, { revalidate: 600 });
    }
  } catch (e) {
    if (e instanceof ApiError && e.status === 429) error = "You are searching faster than the service allows. Wait a few seconds and try again.";
    else if (e instanceof ApiError && e.status === 422) error = "One of the filters has a value the search does not accept. Clear filters and try again.";
    else error = "The search service did not answer. Try again in a minute.";
  }

  const results = data?.results ?? [];
  const total = data?.total ?? 0;
  const pages = Math.min(Math.ceil(total / PAGE_SIZE), state.q ? MAX_SEARCH_PAGES : MAX_BROWSE_PAGES);
  const keep: [string, string][] = [...toParams({ ...state, q: "" }).entries()].filter(([k]) => k !== "sort");
  const firstPageSearch = state.q && state.page === 1;
  const filtersActive = keep.length > 0;

  return (
    <div className={styles.layout}>
      <div className={styles.top}>
        <h1 className="visually-hidden">{state.q ? `Search results for ${state.q}` : "Browse the catalog"}</h1>
        <SearchBalloon defaultValue={state.q} hidden={keep} />
      </div>

      <aside className={styles.side}>
        <FilterPanel className={styles.filterToggle} active={filtersActive}>
          <Filters state={state} facets={facets} />
        </FilterPanel>
      </aside>

      <section className={styles.results} aria-live="polite">
        {error ? (
          <div className="notice" role="alert">
            <h2>No results right now</h2>
            <p>{error}</p>
          </div>
        ) : tooDeep ? (
          <div className="notice">
            <h2>That is as deep as search goes</h2>
            <p>
              Search shows the best {MAX_SEARCH_PAGES * PAGE_SIZE} matches. Add a detail to your description or a filter to
              narrow it down.
            </p>
          </div>
        ) : results.length === 0 ? (
          <div className="notice">
            <h2>Nothing fits that yet</h2>
            <p>
              {state.q
                ? "Try describing the story in different words, or clear some filters."
                : "No titles match these filters. Clear one or two to see more."}
            </p>
          </div>
        ) : (
          <>
            <p className={styles.summary}>
              {state.q ? (
                <>
                  Best {Math.min(total, MAX_SEARCH_PAGES * PAGE_SIZE)} matches for <q>{state.q}</q>
                  {"mode" in data! && data.mode === "keyword" && <>, keyword search only right now</>}
                </>
              ) : (
                <>{total.toLocaleString("en-US")} titles</>
              )}
              {pages > 1 && <>. Page {state.page} of {pages}</>}
            </p>
            <ul className="panels">
              {results.map((c, i) => (
                <ComicCard key={c.id} comic={c} splash={Boolean(firstPageSearch && i === 0)} priority={i < 4} />
              ))}
            </ul>
            {pages > 1 && (
              <nav className={styles.pager} aria-label="Pages">
                {state.page > 1 ? (
                  <Link href={`/search?${toParams(state, { page: String(state.page - 1) })}`} rel="prev">
                    Previous page
                  </Link>
                ) : (
                  <span />
                )}
                {state.page < pages && (
                  <Link href={`/search?${toParams(state, { page: String(state.page + 1) })}`} rel="next">
                    Next page
                  </Link>
                )}
              </nav>
            )}
          </>
        )}
      </section>
    </div>
  );
}
