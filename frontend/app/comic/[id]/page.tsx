import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Cover from "@/components/Cover";
import ResultPanel from "@/components/ResultPanel";
import PeelLink from "@/components/PeelLink";
import { api, fandomUrl, tryApi, type Comic } from "@/lib";

type Props = { params: Promise<{ id: string }> };

async function getComic(id: string) {
  try {
    return await api<Comic>(`/api/comics/${encodeURIComponent(id)}`);
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const comic = await getComic((await params).id);
  return comic ? { title: comic.title, description: comic.description.slice(0, 160) } : { title: "Not found" };
}

const vibeWord = (v: number, low: string, mid: string, high: string) => (v > 0.6 ? high : v < 0.4 ? low : mid);

export default async function ComicPage({ params }: Props) {
  const { id } = await params;
  const comic = await getComic(id);
  if (!comic) notFound();
  const similar = (await tryApi<{ results: Comic[] }>(`/api/comics/${encodeURIComponent(id)}/similar?k=8`))?.results ?? [];
  const facts: [string, string | number | null][] = [
    ["Type", comic.kind],
    ["Started", comic.year],
    ["Status", comic.status],
    ["Publisher", comic.publisher],
    ["AniList score", comic.score ? `★ ${comic.score} / 10` : null],
    [comic.source === "metron" ? "Issues" : "Chapters", comic.chapters],
    ["Creators", comic.creators.join(", ") || null],
  ];

  return (
    <div className="wrap detail-wrap">
      <PeelLink href="/" className="back">
        ← Back to search
      </PeelLink>
      <article className="detail">
        <div className="detail-cover">
          <Cover comic={comic} eager />
        </div>
        <div className="detail-body">
          <h1>{comic.title}</h1>
          {comic.alt_title && <p className="detail-alt">{comic.alt_title}</p>}
          <dl className="facts">
            {facts
              .filter(([, v]) => v)
              .map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
          </dl>
          {[...comic.genres, ...comic.tags].length > 0 && (
            <ul className="tags" aria-label="Genres and themes">
              {[...comic.genres, ...comic.tags].map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          )}
          <p className="detail-desc">{comic.description || "No synopsis on file yet."}</p>
          <div className="detail-vibe">
            <span>
              Tone: <b>{vibeWord(comic.tone, "light", "balanced", "dark")}</b>
            </span>
            <span>
              Scope: <b>{vibeWord(comic.scope, "street-level", "mid", "cosmic")}</b>
            </span>
          </div>
          <div className="detail-links">
            {comic.url && (
              <a className="btn btn-primary" href={comic.url} target="_blank" rel="noreferrer">
                View on {comic.source === "anilist" ? "AniList" : "Metron"} ↗
              </a>
            )}
            <a className="btn btn-fandom" href={fandomUrl(comic)} target="_blank" rel="noreferrer">
              {comic.kind === "Marvel" ? "Marvel Fandom" : comic.kind === "DC" ? "DC Fandom" : "Fandom wiki"} ↗
            </a>
            {comic.wiki_url && (
              <a className="btn" href={comic.wiki_url} target="_blank" rel="noreferrer">
                Wikipedia ↗
              </a>
            )}
          </div>
        </div>
      </article>

      {similar.length > 0 && (
        <section id="similar" aria-labelledby="similar-title">
          <h2 id="similar-title" className="section-title">
            If you like this, try
          </h2>
          <ol className="comic-grid">
            {similar.map((c) => (
              <ResultPanel key={c.id} comic={c} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}
