"""Semantic search over the merged catalog.

Ranking: text similarity is the gatekeeper, tone/scope sliders are a fine-tuner
that can lower a match by at most 30% combined (same rule as v1).
"""
import json
from pathlib import Path

import numpy as np

from .aliases import expand, normalize
from .embedder import HashingEmbedder, get_embedder

VIBE_WEIGHT = 0.15
TITLE_WEIGHT = 0.35  # exact / contained title match, incl. names implied by nicknames
POPULARITY_WEIGHT = 0.05  # small tie-breaker toward well-known series
MIN_SEMANTIC = 0.15  # below this a title is unrelated unless its name matched; keeps "nothing found" honest
PUBLIC_FIELDS = (
    "id", "source", "kind", "title", "alt_title", "description", "genres", "tags", "publisher",
    "creators", "year", "status", "country", "score", "volumes", "chapters", "cover", "color",
    "url", "wiki_url", "tone", "scope",
)


def public(c: dict) -> dict:
    return {k: c.get(k) for k in PUBLIC_FIELDS}


class SearchEngine:
    def __init__(self, catalog: list[dict], vectors: np.ndarray, embedder):
        if len(catalog) != len(vectors):
            raise ValueError("catalog and vectors are out of sync, rebuild the index")
        self.catalog = catalog
        self.vectors = vectors.astype(np.float32)
        self.embedder = embedder
        self.index = {c["id"]: i for i, c in enumerate(catalog)}
        self.tone = np.array([c["tone"] for c in catalog], dtype=np.float32)
        self.scope = np.array([c["scope"] for c in catalog], dtype=np.float32)
        pop = np.array([c.get("popularity") or 0 for c in catalog], dtype=np.float32)
        self.pop_rank = np.argsort(-pop)
        # popularity is on different scales per source, so normalize within each source
        log_pop = np.log1p(pop)
        self.pop_norm = np.zeros_like(log_pop)
        for source in {c["source"] for c in catalog}:
            idx = np.array([c["source"] == source for c in catalog])
            top = log_pop[idx].max() or 1.0
            self.pop_norm[idx] = log_pop[idx] / top
        self.norm_titles = [f" {normalize(c['title'])} " for c in catalog]

    @classmethod
    def load(cls, data_dir: Path) -> "SearchEngine":
        catalog = json.loads((data_dir / "catalog.json").read_text(encoding="utf-8"))
        vectors = np.load(data_dir / "vectors.npy")
        meta_path = data_dir / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        embedder = HashingEmbedder() if meta.get("embedder") == "hashing" else get_embedder()
        return cls(catalog, vectors, embedder)

    def _mask(self, kind: str | None) -> np.ndarray:
        if not kind or kind == "all":
            return np.ones(len(self.catalog), dtype=bool)
        return np.array([c["kind"].lower() == kind.lower() for c in self.catalog])

    def _title_scores(self, candidates: list[str]) -> np.ndarray:
        """1.0 exact title, 0.8 title contains the name, 0.6 query contains the whole title."""
        cands = [f" {normalize(c)} " for c in candidates if len(normalize(c)) >= 3]
        scores = np.zeros(len(self.catalog), dtype=np.float32)
        for i, title in enumerate(self.norm_titles):
            best = 0.0
            for cand in cands:
                if cand == title:
                    best = 1.0
                    break
                if cand in title:
                    best = max(best, 0.8)
                elif len(title) > 5 and title in cand:
                    best = max(best, 0.6)
            scores[i] = best
        return scores

    def search(self, query: str, tone: float = 0.5, scope: float = 0.5, kind: str | None = None, k: int = 12) -> list[dict]:
        names = expand(query)
        text = f"{query}. {', '.join(names)}" if names else query
        q = self.embedder.encode([text])[0]
        semantic = np.clip(self.vectors @ q, 0.0, 1.0)
        modifier = 1.0 - VIBE_WEIGHT * np.abs(self.tone - tone) - VIBE_WEIGHT * np.abs(self.scope - scope)
        title = self._title_scores([query, *names])
        score = semantic * modifier + TITLE_WEIGHT * title + POPULARITY_WEIGHT * self.pop_norm
        relevant = (semantic >= MIN_SEMANTIC) | (title > 0)
        composite = np.where(self._mask(kind) & relevant, score, -1.0)
        top = np.argsort(-composite)[:k]
        return [
            {**public(self.catalog[i]), "match": round(float(semantic[i]), 4), "score_composite": round(float(composite[i]), 4)}
            for i in top
            if composite[i] > 0
        ]

    def get(self, comic_id: str) -> dict | None:
        i = self.index.get(comic_id)
        return None if i is None else public(self.catalog[i])

    def similar(self, comic_id: str, k: int = 8) -> list[dict]:
        i = self.index.get(comic_id)
        if i is None:
            return []
        sims = self.vectors @ self.vectors[i]
        sims[i] = -1.0
        return [{**public(self.catalog[j]), "match": round(float(sims[j]), 4)} for j in np.argsort(-sims)[:k]]

    def trending(self, kind: str | None = None, k: int = 12) -> list[dict]:
        mask = self._mask(kind)
        return [public(self.catalog[i]) for i in self.pop_rank if mask[i]][:k]

    def daily_pick(self, day: int, pool: int = 150) -> dict:
        """Same pick all day, rotates daily through popular titles that have a cover and a description."""
        candidates = [i for i in self.pop_rank if self.catalog[i].get("cover") and len(self.catalog[i].get("description") or "") > 80][:pool]
        if not candidates:
            candidates = list(self.pop_rank[:pool])
        return public(self.catalog[candidates[day % len(candidates)]])

    def random(self, rng: np.random.Generator, kind: str | None = None) -> dict:
        idx = np.flatnonzero(self._mask(kind))
        return public(self.catalog[int(rng.choice(idx))])

    def stats(self) -> dict:
        kinds: dict[str, int] = {}
        for c in self.catalog:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        return {"total": len(self.catalog), "kinds": kinds}
