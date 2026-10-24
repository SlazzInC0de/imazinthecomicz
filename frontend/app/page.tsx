"use client";

import { useEffect, useState } from "react";
import ComicCard from "./ComicCard";
import { api, KINDS, type Comic } from "@/lib";

const EXAMPLES = [
  "a blind lawyer fighting crime at night",
  "weak hero gets a system and levels up alone",
  "quiet story about a girl running a countryside cafe",
  "pirates searching for a legendary treasure",
  "humanity fighting giants behind huge walls",
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [tone, setTone] = useState(0.5);
  const [scope, setScope] = useState(0.5);
  const [kind, setKind] = useState<(typeof KINDS)[number]>("all");
  const [results, setResults] = useState<Comic[]>([]);
  const [heading, setHeading] = useState("Trending now");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<{ results: Comic[] }>(`/api/trending?k=12${kind !== "all" ? `&kind=${kind}` : ""}`)
      .then((d) => {
        if (!query) setResults(d.results);
      })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  async function runSearch(q: string) {
    if (q.trim().length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ q, tone: String(tone), scope: String(scope), k: "12" });
      if (kind !== "all") params.set("kind", kind);
      const data = await api<{ results: Comic[] }>(`/api/search?${params}`);
      setResults(data.results);
      setHeading(data.results.length ? `Results for “${q}”` : `Nothing matched “${q}”`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="hero">
        <form
          className="search"
          onSubmit={(e) => {
            e.preventDefault();
            runSearch(query);
          }}
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe the story you want..."
            aria-label="Describe the story you want"
            maxLength={300}
          />
          <button type="submit" disabled={loading}>
            {loading ? "..." : "POW!"}
          </button>
        </form>

        <div className="examples">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setQuery(ex);
                runSearch(ex);
              }}
            >
              {ex}
            </button>
          ))}
        </div>

        <div className="controls">
          <label className="slider">
            <span>Tone</span>
            <small>campy</small>
            <input type="range" min={0} max={1} step={0.05} value={tone} onChange={(e) => setTone(+e.target.value)} />
            <small>grimdark</small>
          </label>
          <label className="slider">
            <span>Scope</span>
            <small>street</small>
            <input type="range" min={0} max={1} step={0.05} value={scope} onChange={(e) => setScope(+e.target.value)} />
            <small>cosmic</small>
          </label>
          <div className="kinds" role="group" aria-label="Filter by type">
            {KINDS.map((k) => (
              <button key={k} type="button" className={k === kind ? "on" : ""} onClick={() => setKind(k)}>
                {k === "all" ? "All" : k}
              </button>
            ))}
          </div>
        </div>
      </section>

      {error && <p className="error">⚠ {error}</p>}

      <h2 className="section-title">{heading}</h2>
      <section className="grid">
        {results.map((c, i) => (
          <ComicCard key={c.id} comic={c} rank={c.match !== undefined ? i + 1 : undefined} />
        ))}
      </section>
    </>
  );
}
