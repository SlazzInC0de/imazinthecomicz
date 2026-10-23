"""
Hybrid search over the catalog.

Each query is scored two ways:
  * semantic: cosine similarity between the query embedding and each title's
    embedding (synopsis, genres, themes, creators)
  * keyword: BM25 over the same text, with the title counted three times, so
    exact names and character names still win

The two are min-max scaled over the filtered candidates and blended 70 / 30.
A title that equals the query gets a bonus, popularity breaks near-ties, and
the optional vibe sliders scale scores down by distance from the chosen tone
and scope. With no embedding model available the engine falls back to keyword
search instead of failing.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy import sparse

SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.05
VIBE_STRENGTH = 0.35
EXACT_TITLE_BONUS = 0.5
PARTIAL_TITLE_BONUS = 0.15
MAX_RESULTS = 96
# No "strong / good match" label: on eval/queries.json the cosine of relevant and
# irrelevant top-10 hits overlaps almost completely (median 0.610 vs 0.607), so a
# fixed cut-off would mislabel results. Rank order is what carries the signal.

STOPWORDS = set(
    "a an and are as at be by for from has have in into is it its of on or that the their them they this to "
    "was were where which who with about some story stories comic comics manga series like".split()
)
_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)

CARD_FIELDS = ["id", "title", "kind", "format", "year", "status", "score", "genres", "cover", "cover_color",
               "length", "length_unit", "publisher", "creators", "source"]


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if (len(t) > 1 or t.isdigit()) and t not in STOPWORDS]


def normalize_title(text: str) -> str:
    return re.sub(r"[^\w]", "", text.lower())


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.2, b: float = 0.75):
        vocab: dict[str, int] = {}
        rows, cols, vals = [], [], []
        lengths = np.zeros(len(docs))
        for d, tokens in enumerate(docs):
            lengths[d] = len(tokens)
            counts: dict[int, int] = {}
            for tok in tokens:
                idx = vocab.setdefault(tok, len(vocab))
                counts[idx] = counts.get(idx, 0) + 1
            rows.extend([d] * len(counts))
            cols.extend(counts.keys())
            vals.extend(counts.values())
        tf = sparse.csr_matrix((vals, (rows, cols)), shape=(len(docs), len(vocab)), dtype=np.float32)
        df = np.bincount(tf.indices, minlength=len(vocab))
        n = len(docs)
        idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
        norm = k1 * (1 - b + b * lengths / max(lengths.mean(), 1.0))
        tf = tf.tocoo()
        weights = idf[tf.col] * tf.data * (k1 + 1) / (tf.data + norm[tf.row])
        self.matrix = sparse.csc_matrix((weights, (tf.row, tf.col)), shape=tf.shape)
        self.vocab = vocab

    def score(self, tokens: list[str]) -> np.ndarray:
        ids = [self.vocab[t] for t in dict.fromkeys(tokens) if t in self.vocab]
        if not ids:
            return np.zeros(self.matrix.shape[0], dtype=np.float32)
        return np.asarray(self.matrix[:, ids].sum(axis=1)).ravel()


@dataclass
class Filters:
    kinds: list[str] | None = None
    genres: list[str] | None = None
    year_min: int | None = None
    year_max: int | None = None
    status: str | None = None
    min_score: int | None = None


@dataclass
class Hit:
    index: int
    score: float
    semantic: float | None
    keyword: float
    matched: list[str]


def _to_python(value):
    if isinstance(value, np.ndarray):
        return [_to_python(v) for v in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_to_python(v) for v in value]
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


class Catalog:
    def __init__(self, df: pd.DataFrame, vectors: np.ndarray | None, embedder=None, meta: dict | None = None):
        self.df = df.reset_index(drop=True)
        self.meta = meta or {}
        self.embedder = embedder
        self.vectors = None if vectors is None else np.ascontiguousarray(vectors, dtype=np.float32)
        if self.vectors is not None and len(self.vectors) != len(self.df):
            raise ValueError("embeddings and catalog have different lengths")

        self.records = [{k: _to_python(v) for k, v in row.items() if k != "doc"} for row in self.df.to_dict("records")]
        self.by_id = {rec["id"]: i for i, rec in enumerate(self.records)}
        self.titles = [{normalize_title(rec["title"])} | {normalize_title(t) for t in rec["alt_titles"] or []}
                       for rec in self.records]
        bm25_docs = []
        for rec, doc in zip(self.records, self.df["doc"]):
            title_text = " ".join([rec["title"], *(rec["alt_titles"] or [])])
            bm25_docs.append(tokenize(title_text) * 3 + tokenize(doc))
        self.bm25 = BM25(bm25_docs)

        pop = np.log1p(self.df["popularity"].fillna(0).to_numpy(dtype=float))
        self.popularity = pop / max(pop.max(), 1.0)
        self.tone = self.df["tone"].to_numpy(dtype=float)
        self.scope = self.df["scope"].to_numpy(dtype=float)
        self.year = self.df["year"].astype("Float64").to_numpy(dtype=float, na_value=np.nan)
        self.score_col = self.df["score"].astype("Float64").to_numpy(dtype=float, na_value=-1.0)
        self.kind = self.df["kind"].to_numpy()
        self.status = self.df["status"].fillna("").to_numpy()
        self.genre_sets = [set(g or []) for g in self.records_field("genres")]
        self._facets = self._build_facets()

    # ------------------------------------------------------------------ loading
    @classmethod
    def load(cls, data_dir: Path, embedder_factory: Callable[[str], object] | None = None) -> "Catalog":
        df = pd.read_parquet(data_dir / "catalog.parquet")
        meta_path = data_dir / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        vec_path = data_dir / "embeddings.npy"
        vectors = np.load(vec_path) if vec_path.exists() else None
        embedder = None
        if vectors is not None and embedder_factory and meta.get("model"):
            try:
                embedder = embedder_factory(meta["model"])
            except Exception as exc:  # model download or runtime failure
                print(f"Embedding model unavailable, using keyword search only: {exc}")
        return cls(df, vectors, embedder, meta)

    def records_field(self, name: str) -> list:
        return [rec[name] for rec in self.records]

    @property
    def mode(self) -> str:
        return "hybrid" if self.embedder is not None and self.vectors is not None else "keyword"

    # ------------------------------------------------------------------ filters
    def mask(self, f: Filters) -> np.ndarray:
        keep = np.ones(len(self.records), dtype=bool)
        if f.kinds:
            keep &= np.isin(self.kind, f.kinds)
        if f.genres:
            wanted = set(f.genres)
            keep &= np.fromiter((wanted <= g for g in self.genre_sets), dtype=bool, count=len(self.genre_sets))
        if f.year_min is not None:
            keep &= self.year >= f.year_min
        if f.year_max is not None:
            keep &= self.year <= f.year_max
        if f.status:
            keep &= self.status == f.status
        if f.min_score is not None:
            keep &= self.score_col >= f.min_score
        return keep

    def _vibe(self, idx: np.ndarray, tone: float | None, scope: float | None) -> np.ndarray:
        factor = np.ones(len(idx))
        if tone is not None:
            factor *= 1 - VIBE_STRENGTH * np.abs(self.tone[idx] - tone)
        if scope is not None:
            factor *= 1 - VIBE_STRENGTH * np.abs(self.scope[idx] - scope)
        return factor

    # ------------------------------------------------------------------ search
    def search(self, query: str, f: Filters, tone: float | None = None, scope: float | None = None,
               limit: int = 24, offset: int = 0) -> tuple[list[Hit], int]:
        idx = np.flatnonzero(self.mask(f))
        if not len(idx):
            return [], 0
        tokens = tokenize(query)
        keyword = self.bm25.score(tokens)[idx] if tokens else np.zeros(len(idx))
        kw_n = keyword / keyword.max() if keyword.max() > 0 else keyword

        semantic = None
        if self.mode == "hybrid":
            semantic = self.vectors[idx] @ self.embedder.embed_query(query)
            spread = semantic.max() - semantic.min()
            sem_n = (semantic - semantic.min()) / spread if spread > 0 else np.zeros(len(idx))
            combined = SEMANTIC_WEIGHT * sem_n + KEYWORD_WEIGHT * kw_n
        else:
            combined = kw_n.copy()

        qnorm = normalize_title(query)
        exact = np.zeros(len(idx), dtype=bool)
        if len(qnorm) >= 3:
            for pos, i in enumerate(idx):
                titles = self.titles[i]
                if qnorm in titles:
                    exact[pos] = True
                    combined[pos] += EXACT_TITLE_BONUS
                elif len(qnorm) >= 4 and any(qnorm in t for t in titles):
                    combined[pos] += PARTIAL_TITLE_BONUS

        combined += POPULARITY_WEIGHT * self.popularity[idx]
        combined *= self._vibe(idx, tone, scope)

        if semantic is None:
            # a title made only of stopwords ("It", "Us") has no BM25 terms but still matches exactly
            relevant = np.flatnonzero((keyword > 0) | exact)
            order = relevant[np.argsort(-combined[relevant], kind="stable")]
        else:
            order = np.argsort(-combined, kind="stable")
        order = order[:MAX_RESULTS]
        total = len(order)
        q_tokens = set(tokens)
        hits = []
        for pos in order[offset: offset + limit]:
            i = int(idx[pos])
            rec = self.records[i]
            labels = [*(rec["genres"] or []), *(rec["tags"] or [])]
            matched = [lab for lab in labels if q_tokens & set(tokenize(lab))][:4]
            hits.append(Hit(i, float(combined[pos]), None if semantic is None else float(semantic[pos]),
                            float(keyword[pos]), matched))
        return hits, total

    def similar(self, comic_id: str, limit: int = 12) -> list[Hit]:
        i = self.by_id[comic_id]
        if self.vectors is not None:
            sims = self.vectors @ self.vectors[i]
        else:  # keyword fallback: reuse the title's own genres and themes as the query
            rec = self.records[i]
            sims = self.bm25.score(tokenize(" ".join([*(rec["genres"] or []), *(rec["tags"] or [])])))
            sims = sims / max(sims.max(), 1e-9)
        scores = sims + POPULARITY_WEIGHT * self.popularity
        scores[i] = -np.inf
        # skip other entries of the same franchise (sequels share most of their text)
        base = normalize_title(self.records[i]["title"])[:8]
        order = []
        for j in np.argsort(-scores):
            if scores[j] == -np.inf or len(order) == limit:
                break
            if len(base) >= 6 and normalize_title(self.records[j]["title"]).startswith(base):
                continue
            order.append(int(j))
        return [Hit(j, float(scores[j]), float(sims[j]), 0.0, []) for j in order]

    def browse(self, f: Filters, sort: str = "popular", limit: int = 24, offset: int = 0) -> tuple[list[int], int]:
        idx = np.flatnonzero(self.mask(f))
        if sort == "score":
            key = -self.score_col[idx]
        elif sort == "newest":
            key = -np.nan_to_num(self.year[idx], nan=0)
        else:
            key = -self.popularity[idx]
        order = idx[np.argsort(key, kind="stable")]
        return [int(i) for i in order[offset: offset + limit]], len(idx)

    # ------------------------------------------------------------------ output
    def card(self, i: int) -> dict:
        rec = self.records[i]
        out = {k: rec.get(k) for k in CARD_FIELDS}
        out["genres"] = (rec["genres"] or [])[:3]
        out["creators"] = (rec["creators"] or [])[:2]
        out["blurb"] = rec["description"][:240].rsplit(" ", 1)[0] + "…" if len(rec["description"]) > 240 else rec["description"]
        return out

    def detail(self, comic_id: str) -> dict:
        return dict(self.records[self.by_id[comic_id]])

    def _build_facets(self) -> dict:
        genres: dict[str, int] = {}
        for g in self.genre_sets:
            for name in g:
                genres[name] = genres.get(name, 0) + 1
        years = self.year[~np.isnan(self.year)]
        return {
            "total": len(self.records),
            "kinds": {k: int(v) for k, v in pd.Series(self.kind).value_counts().items()},
            "genres": dict(sorted(genres.items(), key=lambda kv: -kv[1])),
            "statuses": sorted(s for s in set(self.status) if s),
            "year_min": int(years.min()) if len(years) else None,
            "year_max": int(years.max()) if len(years) else None,
            "mode": self.mode,
            "built_at": self.meta.get("built_at"),
            "model": self.meta.get("model"),
        }

    def facets(self) -> dict:
        return {**self._facets, "mode": self.mode}
