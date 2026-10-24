"""IMAZINTHECOMICS API.

Run:  uvicorn backend.app:app --reload --port 8000
"""
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .engine import SearchEngine

DATA_DIR = Path(os.environ.get("IMAZIN_DATA", Path(__file__).resolve().parent / "data"))

app = FastAPI(title="IMAZINTHECOMICS API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("IMAZIN_CORS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_engine() -> SearchEngine:
    if not (DATA_DIR / "catalog.json").exists():
        raise HTTPException(503, "Index not built yet. Run the ingest scripts and build_index first.")
    return SearchEngine.load(DATA_DIR)


@app.get("/api/health")
def health():
    return {"status": "ok", "index_ready": (DATA_DIR / "catalog.json").exists()}


@app.get("/api/stats")
def stats(engine: SearchEngine = Depends(get_engine)):
    return engine.stats()


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=2, max_length=300),
    tone: float = Query(0.5, ge=0, le=1),
    scope: float = Query(0.5, ge=0, le=1),
    kind: str | None = Query(None, pattern="^(all|Manga|Manhwa|Manhua|Marvel|DC|Western|One-shot|Light novel)$"),
    k: int = Query(12, ge=1, le=50),
    engine: SearchEngine = Depends(get_engine),
):
    return {"query": q, "results": engine.search(q, tone=tone, scope=scope, kind=kind, k=k)}


@app.get("/api/trending")
def trending(kind: str | None = None, k: int = Query(12, ge=1, le=50), engine: SearchEngine = Depends(get_engine)):
    return {"results": engine.trending(kind, k)}


@app.get("/api/pick")
def pick(engine: SearchEngine = Depends(get_engine)):
    return engine.daily_pick(date.today().toordinal())


@app.get("/api/random")
def random_comic(kind: str | None = None, engine: SearchEngine = Depends(get_engine)):
    return engine.random(np.random.default_rng(), kind)


@app.get("/api/comics/{comic_id}")
def comic(comic_id: str, engine: SearchEngine = Depends(get_engine)):
    item = engine.get(comic_id)
    if item is None:
        raise HTTPException(404, "Comic not found")
    return item


@app.get("/api/comics/{comic_id}/similar")
def similar(comic_id: str, k: int = Query(8, ge=1, le=24), engine: SearchEngine = Depends(get_engine)):
    if engine.get(comic_id) is None:
        raise HTTPException(404, "Comic not found")
    return {"results": engine.similar(comic_id, k)}
