import ComicCard from "../../ComicCard";
import { api, wikiUrl, type Comic } from "@/lib";

export default async function ComicPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let comic: Comic;
  let similar: Comic[] = [];
  try {
    comic = await api<Comic>(`/api/comics/${encodeURIComponent(id)}`);
    similar = (await api<{ results: Comic[] }>(`/api/comics/${encodeURIComponent(id)}/similar?k=8`)).results;
  } catch (e) {
    return (
      <div className="detail-missing">
        <h2>Comic not found</h2>
        <p>{(e as Error).message}</p>
        <a href="/">← Back to search</a>
      </div>
    );
  }

  return (
    <>
      <a href="/" className="back">
        ← Back to search
      </a>
      <article className="detail" style={{ ["--accent" as string]: comic.color ?? "#ffd43b" }}>
        <div className="detail-cover">
          {comic.cover ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={comic.cover} alt={`${comic.title} cover`} />
          ) : (
            <div className="cover-fallback">{comic.title}</div>
          )}
        </div>
        <div className="detail-body">
          <span className="badge">{comic.kind}</span>
          <h1>{comic.title}</h1>
          {comic.alt_title && <p className="alt">{comic.alt_title}</p>}
          <dl className="facts">
            {comic.year && (<><dt>Started</dt><dd>{comic.year}</dd></>)}
            {comic.status && (<><dt>Status</dt><dd>{comic.status}</dd></>)}
            {comic.publisher && (<><dt>Publisher</dt><dd>{comic.publisher}</dd></>)}
            {comic.score && (<><dt>Score</dt><dd>★ {comic.score} / 10</dd></>)}
            {comic.chapters && (<><dt>{comic.source === "metron" ? "Issues" : "Chapters"}</dt><dd>{comic.chapters}</dd></>)}
            {comic.creators.length > 0 && (<><dt>Creators</dt><dd>{comic.creators.join(", ")}</dd></>)}
          </dl>
          <div className="chips">
            {[...comic.genres, ...comic.tags].map((g) => (
              <span key={g}>{g}</span>
            ))}
          </div>
          <p className="desc">{comic.description || "No description available."}</p>
          <div className="vibe">
            <div>
              Tone <meter min={0} max={1} value={comic.tone} /> {comic.tone > 0.6 ? "dark" : comic.tone < 0.4 ? "light" : "balanced"}
            </div>
            <div>
              Scope <meter min={0} max={1} value={comic.scope} /> {comic.scope > 0.6 ? "cosmic" : comic.scope < 0.4 ? "street-level" : "mid"}
            </div>
          </div>
          <div className="links">
            {comic.url && (
              <a className="source-link" href={comic.url} target="_blank" rel="noreferrer">
                View on {comic.source === "anilist" ? "AniList" : "Metron"} ↗
              </a>
            )}
            <a className="source-link wiki" href={wikiUrl(comic.title)} target="_blank" rel="noreferrer">
              Wikipedia ↗
            </a>
          </div>
        </div>
      </article>

      <h2 className="section-title">If you like this, try</h2>
      <section className="grid">
        {similar.map((c) => (
          <ComicCard key={c.id} comic={c} />
        ))}
      </section>
    </>
  );
}
