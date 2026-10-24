import Cover from "./Cover";
import PeelLink from "./PeelLink";
import { tryApi, type Comic } from "@/lib";

const KINDS = ["Manga", "Manhwa", "Manhua", "Marvel", "DC", "Western"];

export default async function Ticker() {
  const tops = await Promise.all(KINDS.map((k) => tryApi<{ results: Comic[] }>(`/api/trending?kind=${k}&k=1`)));
  const items = tops.map((t, i) => ({ kind: KINDS[i], comic: t?.results[0] })).filter((x) => x.comic) as { kind: string; comic: Comic }[];
  if (!items.length) return null;
  return (
    <section className="ticker" aria-label="Most popular in each category">
      <h2 className="ticker-hd">Trending now</h2>
      <ol className="ticker-list">
        {items.map(({ kind, comic }) => (
          <li key={kind}>
            <PeelLink href={`/comic/${comic.id}`} className="ticker-it">
              <span className="ticker-cv">
                <Cover comic={comic} />
              </span>
              <span>
                <b>{comic.title}</b>
                <small>#1 in {kind}</small>
              </span>
            </PeelLink>
          </li>
        ))}
      </ol>
    </section>
  );
}
