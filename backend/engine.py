"""Semantic search over the merged catalog.

Ranking: text similarity is the gatekeeper, tone/scope sliders are a fine-tuner
that can lower a match by at most 30% combined (same rule as v1).
"""
import json
from pathlib import Path

import numpy as np

from .embedder import HashingEmbedder, get_embedder

VIBE_WEIGHT = 0.15
PUBLIC_FIELDS = (
    "id", "source", "kind", "title", "alt_title", "description", "genres", "tags", "publisher",
    "creators", "year", "status", "country", "score", "volumes", "chapters", "cover", "color",
    "url", "tone", "scope",
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

    def search(self, query: str, tone: float = 0.5, scope: float = 0.5, kind: str | None = None, k: int = 12) -> list[dict]:
        q = self.embedder.encode([query])[0]
        semantic = np.clip(self.vectors @ q, 0.0, 1.0)
        modifier = 1.0 - VIBE_WEIGHT * np.abs(self.tone - tone) - VIBE_WEIGHT * np.abs(self.scope - scope)
        composite = np.where(self._mask(kind), semantic * modifier, -1.0)
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

    def stats(self) -> dict:
        kinds: dict[str, int] = {}
        for c in self.catalog:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        return {"total": len(self.catalog), "kinds": kinds}
