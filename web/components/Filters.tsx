"use client";

import { useRef, useState } from "react";

import type { Facets } from "@/lib/types";

export type FilterState = {
  q: string;
  kind: string[];
  genre: string[];
  year_min: string;
  year_max: string;
  status: string;
  min_score: string;
  tone: string;
  scope: string;
  sort: string;
};

const KINDS = ["Manga", "Manhwa", "Manhua", "Western"];

function Vibe(props: {
  name: "tone" | "scope";
  title: string;
  low: string;
  high: string;
  value: string;
  onChange: () => void;
}) {
  const [on, setOn] = useState(props.value !== "");
  return (
    <fieldset className="vibe">
      <legend>
        <label>
          <input
            type="checkbox"
            checked={on}
            onChange={(e) => {
              setOn(e.target.checked);
              // let React disable the slider first, so it drops out of the form
              setTimeout(props.onChange, 0);
            }}
          />{" "}
          {props.title}
        </label>
      </legend>
      <input
        type="range"
        name={props.name}
        min={0}
        max={1}
        step={0.05}
        defaultValue={props.value || "0.5"}
        disabled={!on}
        aria-label={`${props.title}: ${props.low} to ${props.high}`}
        // submit when the thumb is let go, not on every step while dragging
        onPointerUp={props.onChange}
        onKeyUp={(e) => {
          if (e.key.startsWith("Arrow") || e.key === "Home" || e.key === "End") props.onChange();
        }}
      />
      <div className="vibe-ends" aria-hidden="true">
        <span>{props.low}</span>
        <span>{props.high}</span>
      </div>
    </fieldset>
  );
}

export default function Filters({ state, facets }: { state: FilterState; facets: Facets | null }) {
  const form = useRef<HTMLFormElement>(null);
  const submit = () => form.current?.requestSubmit();
  const genres = facets ? Object.keys(facets.genres) : [];
  const browsing = !state.q;

  return (
    <form
      ref={form}
      action="/search"
      method="get"
      className="filters"
      aria-label="Filters"
      onSubmit={(e) => {
        // leave empty fields out of the URL (?q=x&kind=Manga, not &year_min=&status=)
        for (const el of Array.from(e.currentTarget.elements)) {
          if ((el instanceof HTMLInputElement || el instanceof HTMLSelectElement) && el.name && el.value === "") {
            el.disabled = true;
          }
        }
      }}
    >
      {state.q && <input type="hidden" name="q" value={state.q} />}

      <fieldset>
        <legend>Kind</legend>
        {KINDS.map((k) => (
          <label key={k} className="check">
            <input type="checkbox" name="kind" value={k} defaultChecked={state.kind.includes(k)} onChange={submit} />
            {k}
            {facets?.kinds[k] != null && <span className="count">{facets.kinds[k].toLocaleString("en-US")}</span>}
          </label>
        ))}
      </fieldset>

      <details open={state.genre.length > 0}>
        <summary>Genre{state.genre.length > 0 && <span className="count">{state.genre.length} picked</span>}</summary>
        <div className="genre-list">
          {genres.map((g) => (
            <label key={g} className="check">
              <input type="checkbox" name="genre" value={g} defaultChecked={state.genre.includes(g)} onChange={submit} />
              {g}
            </label>
          ))}
        </div>
      </details>

      <fieldset className="years">
        <legend>Started between</legend>
        {/* typing both years then pressing Enter or Apply submits; no submit on blur mid-range */}
        <input
          type="number"
          name="year_min"
          inputMode="numeric"
          min={facets?.year_min ?? 1900}
          max={facets?.year_max ?? 2100}
          placeholder={String(facets?.year_min ?? 1950)}
          defaultValue={state.year_min}
          aria-label="From year"
        />
        <span aria-hidden="true">and</span>
        <input
          type="number"
          name="year_max"
          inputMode="numeric"
          min={facets?.year_min ?? 1900}
          max={facets?.year_max ?? 2100}
          placeholder={String(facets?.year_max ?? 2026)}
          defaultValue={state.year_max}
          aria-label="To year"
        />
      </fieldset>

      <label className="field">
        Status
        <select name="status" defaultValue={state.status} onChange={submit}>
          <option value="">Any</option>
          {(facets?.statuses ?? ["Completed", "Ongoing", "Hiatus", "Cancelled"]).map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>

      <label className="field">
        Reader score
        <select name="min_score" defaultValue={state.min_score} onChange={submit}>
          <option value="">Any</option>
          <option value="60">60 or higher</option>
          <option value="70">70 or higher</option>
          <option value="80">80 or higher</option>
        </select>
      </label>

      {browsing ? (
        <label className="field">
          Order
          <select name="sort" defaultValue={state.sort || "popular"} onChange={submit}>
            <option value="popular">Most read</option>
            <option value="score">Highest scored</option>
            <option value="newest">Newest</option>
          </select>
        </label>
      ) : (
        <div className="vibes">
          <p className="hint">Nudge the results. Off means no preference.</p>
          <Vibe name="tone" title="Tone" low="Lighter" high="Darker" value={state.tone} onChange={submit} />
          <Vibe name="scope" title="Scale" low="Grounded" high="World-ending" value={state.scope} onChange={submit} />
        </div>
      )}

      <div className="filter-actions">
        <button type="submit" className="btn quiet">
          Apply
        </button>
        <a href={state.q ? `/search?q=${encodeURIComponent(state.q)}` : "/search"}>Clear filters</a>
      </div>
    </form>
  );
}
