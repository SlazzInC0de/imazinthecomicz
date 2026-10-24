import Cover from "./Cover";
import HeroDots from "./HeroDots";
import PeelLink from "./PeelLink";
import { shortText, tryApi, type Comic } from "@/lib";

export default async function Hero() {
  const [pick, trending, stats] = await Promise.all([
    tryApi<Comic>("/api/pick"),
    tryApi<{ results: Comic[] }>("/api/trending?k=12"),
    tryApi<{ total: number }>("/api/stats"),
  ]);
  if (!pick) {
    return (
      <section className="hero hero-offline">
        <HeroDots />
        <div className="hero-in">
          <div>
            <h1 className="hero-title">IMAZINTHECOMICS</h1>
            <p className="hero-say">The search API isn&apos;t running yet. Start it with <code>uvicorn backend.app:app --port 8000</code>.</p>
          </div>
        </div>
      </section>
    );
  }
  const fan = (trending?.results ?? []).filter((c) => c.cover && c.id !== pick.id).slice(0, 3);
  const total = stats?.total ? (stats.total < 100 ? String(stats.total) : `${(Math.floor(stats.total / 100) * 100).toLocaleString("en-US")}+`) : null;

  return (
    <section className="hero" aria-labelledby="pick-title">
      <HeroDots />
      <p className="hero-caption">Today&apos;s pick</p>
      <div className="hero-in">
        <div className="hero-copy">
          <h1 id="pick-title" className="hero-title" data-long={pick.title.length > 14 || undefined}>
            {pick.title}
          </h1>
          <p className="hero-say">
            {shortText(pick.description, 190)}
            <span className="hero-meta">
              {pick.kind} · {pick.year}
              {pick.score ? ` · ★ ${pick.score} on AniList` : ""}
            </span>
          </p>
          <div className="hero-actions">
            <PeelLink href={`/comic/${pick.id}`} className="btn btn-primary">
              Open the file
            </PeelLink>
            <PeelLink href={`/comic/${pick.id}#similar`} className="btn">
              More like this
            </PeelLink>
          </div>
        </div>
        <div className="hero-fan" aria-hidden="true">
          {[...fan, pick].map((c, i) => (
            <div key={c.id} className={`fan-cv fan-${i}`}>
              <Cover comic={c} eager />
            </div>
          ))}
          {total && (
            <div className="hero-burst">
              <svg viewBox="0 0 170 130">
                <path d="M85 2 L100 30 L140 8 L130 44 L168 48 L136 70 L160 104 L118 96 L112 128 L86 104 L58 128 L54 94 L10 108 L34 74 L2 54 L40 44 L26 8 L68 30Z" />
              </svg>
              <b>
                {total}
                <br />
                titles!
              </b>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
