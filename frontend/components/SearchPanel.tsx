"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import ResultPanel from "./ResultPanel";
import { api, KINDS, type Comic, type Kind } from "@/lib";

const EXAMPLES = [
  "web swinger who cracks jokes",
  "a blind lawyer fighting crime at night",
  "weak hero gets a system and levels up alone",
  "quiet story about a countryside cafe",
  "humanity fighting giants behind huge walls",
];
const PAGE_SLOTS = 7; // the comic-page layout has 7 shaped slots, the rest flow into a plain grid

type View = "page" | "grid";
type Initial = { q: string; kind: Kind; tone: number; scope: number; view: View };

export default function SearchPanel({ initial }: { initial: Initial }) {
  const router = useRouter();
  const pathname = usePathname();
  const [q, setQ] = useState(initial.q);
  const [tone, setTone] = useState(initial.tone);
  const [scope, setScope] = useState(initial.scope);
  const [kind, setKind] = useState<Kind>(initial.kind);
  const [view, setView] = useState<View>(initial.view);
  const [results, setResults] = useState<Comic[]>([]);
  const [active, setActive] = useState(initial.q); // the query the results belong to
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");
  const [shake, setShake] = useState(false);
  const request = useRef(0);

  const syncUrl = useCallback(
    (next: Partial<Initial>) => {
      const s = { q: active, kind, tone, scope, view, ...next };
      const params = new URLSearchParams();
      if (s.q) params.set("q", s.q);
      if (s.kind !== "all") params.set("kind", s.kind);
      if (s.tone !== 0.5) params.set("tone", String(s.tone));
      if (s.scope !== 0.5) params.set("scope", String(s.scope));
      if (s.view !== "page") params.set("view", s.view);
      const qs = params.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [active, kind, tone, scope, view, pathname, router],
  );

  const load = useCallback(
    async (query: string, opts: { kind: Kind; tone: number; scope: number }) => {
      const id = ++request.current;
      setStatus("loading");
      setError("");
      try {
        let data: { results: Comic[] };
        if (query.trim().length >= 2) {
          const p = new URLSearchParams({ q: query.trim(), tone: String(opts.tone), scope: String(opts.scope), k: "16" });
          if (opts.kind !== "all") p.set("kind", opts.kind);
          data = await api(`/api/search?${p}`);
        } else {
          data = await api(`/api/trending?k=16${opts.kind !== "all" ? `&kind=${opts.kind}` : ""}`);
        }
        if (id !== request.current) return; // a newer request already won
        setResults(data.results);
        setActive(query.trim());
        setStatus("idle");
      } catch (e) {
        if (id !== request.current) return;
        setError((e as Error).message);
        setStatus("error");
      }
    },
    [],
  );

  // First load, and whenever a filter changes, re-run the current query.
  // Debounced so dragging a slider doesn't fire a request per step.
  useEffect(() => {
    const t = setTimeout(() => load(active, { kind, tone, scope }), 180);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, tone, scope, load]);

  // Nav links (/?kind=Manga) change the URL from outside this component.
  useEffect(() => setKind(initial.kind), [initial.kind]);

  function submit(query: string) {
    if (query.trim().length < 2) return;
    setQ(query);
    setShake(true);
    load(query, { kind, tone, scope });
    syncUrl({ q: query.trim() });
  }

  const heading = active ? `Results for "${active}"` : kind === "all" ? "Popular right now" : `Popular in ${kind}`;
  const paged = view === "page" ? results.slice(0, PAGE_SLOTS) : [];
  const rest = view === "page" ? results.slice(PAGE_SLOTS) : results;

  return (
    <section className="finder" aria-labelledby="finder-title">
      <h2 id="finder-title" className="sr-only">
        Search comics
      </h2>
      <form
        className="search"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          submit(q);
        }}
      >
        <label htmlFor="q" className="sr-only">
          Describe the story you want
        </label>
        <input
          id="q"
          name="q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Describe the story you want..."
          maxLength={300}
          autoComplete="off"
        />
        <button type="submit" className={`pow${shake ? " pow-hit" : ""}`} onAnimationEnd={() => setShake(false)} disabled={status === "loading"}>
          <svg viewBox="0 0 220 170" aria-hidden="true">
            <path d="M110 4 L128 46 L176 14 L160 62 L216 60 L172 92 L210 128 L156 118 L160 166 L120 132 L96 168 L86 124 L30 150 L56 106 L4 92 L54 70 L22 30 L74 46 L82 2Z" />
          </svg>
          <span>{status === "loading" ? "..." : "POW!"}</span>
        </button>
      </form>

      <div className="examples">
        <span className="examples-hd">Try</span>
        <ul>
          {EXAMPLES.map((ex) => (
            <li key={ex}>
              <button type="button" className="chip" onClick={() => submit(ex)}>
                {ex}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="controls">
        <label className="vibe">
          <span className="vibe-name">Tone</span>
          <span className="vibe-end">campy</span>
          <input type="range" min={0} max={1} step={0.05} value={tone} onChange={(e) => setTone(+e.target.value)} onMouseUp={() => syncUrl({ tone })} onKeyUp={() => syncUrl({ tone })} aria-valuetext={tone < 0.35 ? "campy" : tone > 0.65 ? "grimdark" : "balanced"} />
          <span className="vibe-end">grimdark</span>
        </label>
        <label className="vibe">
          <span className="vibe-name">Scope</span>
          <span className="vibe-end">street</span>
          <input type="range" min={0} max={1} step={0.05} value={scope} onChange={(e) => setScope(+e.target.value)} onMouseUp={() => syncUrl({ scope })} onKeyUp={() => syncUrl({ scope })} aria-valuetext={scope < 0.35 ? "street-level" : scope > 0.65 ? "cosmic" : "mid"} />
          <span className="vibe-end">cosmic</span>
        </label>
        <div className="kinds" role="group" aria-label="Filter by type">
          {KINDS.map((k) => (
            <button
              key={k}
              type="button"
              aria-pressed={k === kind}
              onClick={() => {
                setKind(k);
                syncUrl({ kind: k });
              }}
            >
              {k === "all" ? "All" : k}
            </button>
          ))}
        </div>
      </div>

      <div className="results-hd">
        <h2>{heading}</h2>
        <p className="results-count" aria-live="polite">
          {status === "loading" ? "Searching..." : status === "error" ? "" : `${results.length} title${results.length === 1 ? "" : "s"}`}
        </p>
        <div className="view-toggle" role="group" aria-label="Layout">
          <button type="button" aria-pressed={view === "page"} onClick={() => { setView("page"); syncUrl({ view: "page" }); }}>
            Comic page
          </button>
          <button type="button" aria-pressed={view === "grid"} onClick={() => { setView("grid"); syncUrl({ view: "grid" }); }}>
            Grid
          </button>
        </div>
      </div>

      {status === "error" && (
        <p className="notice notice-error" role="alert">
          Couldn&apos;t reach the search API: {error}
        </p>
      )}
      {status === "idle" && active && results.length === 0 && (
        <div className="notice">
          <p>
            Nothing matched &quot;{active}&quot;{kind !== "all" ? ` in ${kind}` : ""}.
          </p>
          {kind !== "all" && (
            <button type="button" className="btn" onClick={() => setKind("all")}>
              Search all types
            </button>
          )}
        </div>
      )}

      <div className={status === "loading" ? "results is-loading" : "results"}>
        {paged.length > 0 && (
          <ol className="comic-page">
            {paged.map((c, i) => (
              <ResultPanel key={c.id} comic={c} slot={i} rank={active ? i + 1 : undefined} />
            ))}
          </ol>
        )}
        {rest.length > 0 && (
          <ol className="comic-grid" start={paged.length + 1}>
            {rest.map((c, i) => (
              <ResultPanel key={c.id} comic={c} rank={active ? paged.length + i + 1 : undefined} />
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
