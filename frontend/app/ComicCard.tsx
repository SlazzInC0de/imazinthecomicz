import type { Comic } from "@/lib";

export default function ComicCard({ comic, rank }: { comic: Comic; rank?: number }) {
  return (
    <a href={`/comic/${comic.id}`} className="panel" style={{ ["--accent" as string]: comic.color ?? "#ffd43b" }}>
      <div className="cover">
        {comic.cover ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={comic.cover} alt={`${comic.title} cover`} loading="lazy" />
        ) : (
          <div className="cover-fallback">{comic.title}</div>
        )}
        <span className={`badge badge-${comic.kind.toLowerCase().replace(/\s/g, "")}`}>{comic.kind}</span>
        {rank !== undefined && <span className="rank">#{rank}</span>}
      </div>
      <div className="panel-body">
        <h3>{comic.title}</h3>
        <p className="meta">
          {[comic.year, comic.publisher, comic.score ? `★ ${comic.score}` : null].filter(Boolean).join(" · ")}
        </p>
        <p className="genres">{comic.genres.slice(0, 3).join(" / ")}</p>
        {comic.match !== undefined && (
          <div className="match" title="Semantic match">
            <div style={{ width: `${Math.round(comic.match * 100)}%` }} />
            <span>{Math.round(comic.match * 100)}% match</span>
          </div>
        )}
      </div>
    </a>
  );
}
