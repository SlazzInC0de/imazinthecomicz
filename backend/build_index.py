"""Merge raw AniList + Metron dumps into one catalog and embed it.

Usage:
    python -m backend.build_index
Outputs backend/data/catalog.json and backend/data/vectors.npy
"""
import json
from pathlib import Path

import numpy as np

from .embedder import get_embedder
from .normalize import from_anilist, from_metron, is_comic_page, semantic_doc
from .vibe import scope_score, tone_score

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_DIR = DATA_DIR / "raw"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def build_catalog(raw_dir: Path = RAW_DIR) -> list[dict]:
    catalog = [from_anilist(m) for m in _read_jsonl(raw_dir / "anilist.jsonl")]
    catalog += [from_metron(s) for s in _read_jsonl(raw_dir / "metron.jsonl")]
    wiki = {
        w["id"]: w for w in _read_jsonl(raw_dir / "wiki.jsonl")
        if w.get("wiki_extract") and is_comic_page(w.get("wiki_title", ""), w["wiki_extract"])
    }
    seen, unique = set(), []
    for c in catalog:
        key = (c["title"].lower(), c["source"], c["year"])
        if key in seen:
            continue
        seen.add(key)
        w = wiki.get(c["id"])
        c["wiki_extract"] = w["wiki_extract"] if w else None
        c["wiki_url"] = w.get("wiki_url") if w else None
        if not c["description"] and c["wiki_extract"]:
            c["description"] = c["wiki_extract"]
        c["tone"] = round(tone_score(c["genres"], c["tags"]), 3)
        c["scope"] = round(scope_score(c["genres"], c["tags"]), 3)
        c["doc"] = semantic_doc(c)
        unique.append(c)
    return unique


def build(raw_dir: Path = RAW_DIR, out_dir: Path = DATA_DIR, embedder=None) -> int:
    catalog = build_catalog(raw_dir)
    if not catalog:
        raise SystemExit("No raw data found. Run the AniList / Metron ingest scripts first.")
    embedder = embedder or get_embedder()
    vectors = embedder.encode([c["doc"] for c in catalog])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    np.save(out_dir / "vectors.npy", vectors)
    (out_dir / "meta.json").write_text(json.dumps({"embedder": embedder.name, "count": len(catalog)}))
    return len(catalog)


if __name__ == "__main__":
    n = build()
    print(f"Indexed {n} titles into {DATA_DIR}")
