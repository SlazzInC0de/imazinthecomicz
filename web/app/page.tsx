import Link from "next/link";

import ComicCard from "@/components/ComicCard";
import SearchBalloon from "@/components/SearchBalloon";
import { api } from "@/lib/api";
import type { BrowseResponse, Facets } from "@/lib/types";

import styles from "./home.module.css";

// rendered per request so an API outage is never cached; the fetches themselves are cached for an hour
export const dynamic = "force-dynamic";

const EXAMPLES = [
  "a detective who can see ghosts",
  "a chef cooking in a fantasy world",
  "high school volleyball underdogs",
  "revenge after being betrayed by his party",
  "quiet slice of life in the countryside",
  "space pirates with a bounty on their heads",
];

const SHELVES: { kind: string; title: string }[] = [
  { kind: "Manga", title: "Manga people keep reading" },
  { kind: "Manhwa", title: "Manhwa people keep reading" },
  { kind: "Western", title: "Long-running Western series" },
];

async function load() {
  const facets = await api<Facets>("/api/facets", undefined, { revalidate: 3600 }).catch(() => null);
  if (!facets) return { facets: null, shelves: [] };
  // each shelf loads on its own, so one failed category does not hide the others
  const settled = await Promise.allSettled(
    SHELVES.filter((s) => (facets.kinds[s.kind] ?? 0) > 0).map(async (s) => ({
      ...s,
      items: (
        await api<BrowseResponse>("/api/browse", new URLSearchParams({ kind: s.kind, limit: "12" }), {
          revalidate: 3600,
        })
      ).results,
    })),
  );
  const shelves = settled.flatMap((r) => (r.status === "fulfilled" ? [r.value] : []));
  return { facets, shelves };
}

export default async function Home() {
  const { facets, shelves } = await load();
  return (
    <>
      <section className={`blueline ${styles.hero}`} aria-labelledby="ask">
        <h1 id="ask" className={styles.title}>
          What do you feel like reading?
        </h1>
        <p className={styles.lede}>
          Describe the plot, the mood or a character. You get manga, manhwa, manhua and Western comics that fit, even
          when they use none of your words.
        </p>
        <div className="ask">
          <SearchBalloon />
          <ul className="examples" aria-label="Example searches">
            {EXAMPLES.map((q) => (
              <li key={q}>
                <Link href={`/search?q=${encodeURIComponent(q)}`}>{q}</Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {facets && (
        <p className={styles.count}>
          {facets.total.toLocaleString("en-US")} titles
          {facets.built_at && <>, catalog rebuilt on {formatDate(facets.built_at)}</>}.
        </p>
      )}

      {!facets && (
        <div className="notice" role="status">
          <h2>Search is offline</h2>
          <p>The catalog service did not answer. Try again in a minute.</p>
        </div>
      )}

      {shelves.map((shelf) => (
        <section key={shelf.kind} className={styles.shelf} aria-labelledby={`shelf-${shelf.kind}`}>
          <div className={styles.shelfHead}>
            <h2 id={`shelf-${shelf.kind}`}>{shelf.title}</h2>
            <Link href={`/search?kind=${shelf.kind}`}>All {shelf.kind.toLowerCase()}</Link>
          </div>
          <ul className="panels">
            {shelf.items.map((c) => (
              <ComicCard key={c.id} comic={c} />
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}

function formatDate(iso: string) {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}
