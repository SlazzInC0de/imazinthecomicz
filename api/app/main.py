"""IMAZINTHECOMICS read-only search API."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .engine import Catalog, Filters
from .ratelimit import TokenBucket, client_key
from .settings import Settings, get_settings

log = logging.getLogger("imazin")

Kind = Literal["Manga", "Manhwa", "Manhua", "Western"]
Sort = Literal["popular", "score", "newest"]
ID_PATTERN = r"^(al|cv|mt)-\d{1,9}$"


def create_app(settings: Settings | None = None, catalog: Catalog | None = None) -> FastAPI:
    settings = settings or get_settings()
    bucket = TokenBucket(settings.rate_per_minute, settings.rate_burst)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if catalog is None:
            from .embedder import FastEmbedder

            app.state.catalog = Catalog.load(settings.data_dir, FastEmbedder)
        else:
            app.state.catalog = catalog
        log.info("catalog ready: %s titles, %s mode", len(app.state.catalog.records), app.state.catalog.mode)
        yield

    app = FastAPI(
        title="IMAZINTHECOMICS API",
        version="2.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET"],
        allow_headers=[],
        max_age=600,
    )

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            key = client_key(request, settings.proxy_key, settings.trust_forwarded_for)
            allowed, retry = bucket.allow(key) if key else (True, 0.0)
            if not allowed:
                return JSONResponse({"detail": "Too many requests, slow down a little."}, status_code=429,
                                    headers={"Retry-After": str(int(retry) + 1)})
        try:
            response = await call_next(request)
        except Exception:  # never leak stack traces to clients
            log.exception("unhandled error on %s", request.url.path)
            response = JSONResponse({"detail": "Something went wrong."}, status_code=500)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        if not request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if request.method == "GET" and response.status_code == 200 and request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "public, max-age=300")
        return response

    def catalog_of(request: Request) -> Catalog:
        return request.app.state.catalog

    def filters(kind, genre, year_min, year_max, status, min_score) -> Filters:
        if year_min is not None and year_max is not None and year_min > year_max:
            raise HTTPException(422, "year_min must not be greater than year_max")
        return Filters(kinds=kind or None, genres=genre or None, year_min=year_min, year_max=year_max,
                       status=status, min_score=min_score)

    @app.get("/api/health")
    def health(request: Request):
        cat = catalog_of(request)
        return {"ok": True, "titles": len(cat.records), "mode": cat.mode}

    @app.get("/api/facets")
    def facets(request: Request):
        return catalog_of(request).facets()

    @app.get("/api/search")
    def search(
        request: Request,
        q: str = Query(..., min_length=1, max_length=200),
        kind: list[Kind] = Query(default=[]),
        genre: list[str] = Query(default=[], max_length=6),
        year_min: int | None = Query(None, ge=1900, le=2100),
        year_max: int | None = Query(None, ge=1900, le=2100),
        status: Literal["Completed", "Ongoing", "Hiatus", "Cancelled"] | None = None,
        min_score: int | None = Query(None, ge=0, le=100),
        tone: float | None = Query(None, ge=0, le=1),
        scope: float | None = Query(None, ge=0, le=1),
        limit: int = Query(24, ge=1, le=48),
        offset: int = Query(0, ge=0, le=95),
    ):
        query = " ".join(q.split())
        if not query:
            raise HTTPException(422, "Query is empty.")
        if any(len(g) > 40 for g in genre):
            raise HTTPException(422, "Genre name too long.")
        cat = catalog_of(request)
        started = time.perf_counter()
        hits, total = cat.search(query, filters(kind, genre, year_min, year_max, status, min_score),
                                 tone, scope, limit, offset)
        results = []
        for hit in hits:
            card = cat.card(hit.index)
            card["match"] = {"label": cat.match_label(hit.semantic), "matched": hit.matched,
                             "semantic": None if hit.semantic is None else round(hit.semantic, 4),
                             "score": round(hit.score, 4)}
            results.append(card)
        return {"query": query, "mode": cat.mode, "total": total, "offset": offset,
                "took_ms": round((time.perf_counter() - started) * 1000, 1), "results": results}

    @app.get("/api/browse")
    def browse(
        request: Request,
        kind: list[Kind] = Query(default=[]),
        genre: list[str] = Query(default=[], max_length=6),
        year_min: int | None = Query(None, ge=1900, le=2100),
        year_max: int | None = Query(None, ge=1900, le=2100),
        status: Literal["Completed", "Ongoing", "Hiatus", "Cancelled"] | None = None,
        min_score: int | None = Query(None, ge=0, le=100),
        sort: Sort = "popular",
        limit: int = Query(24, ge=1, le=48),
        offset: int = Query(0, ge=0, le=5000),
    ):
        cat = catalog_of(request)
        idx, total = cat.browse(filters(kind, genre, year_min, year_max, status, min_score), sort, limit, offset)
        return {"total": total, "offset": offset, "results": [cat.card(i) for i in idx]}

    @app.get("/api/comics/{comic_id}")
    def comic(request: Request, comic_id: str = Path(..., pattern=ID_PATTERN)):
        cat = catalog_of(request)
        if comic_id not in cat.by_id:
            raise HTTPException(404, "No comic with that id.")
        return cat.detail(comic_id)

    @app.get("/api/comics/{comic_id}/similar")
    def similar(request: Request, comic_id: str = Path(..., pattern=ID_PATTERN), limit: int = Query(12, ge=1, le=24)):
        cat = catalog_of(request)
        if comic_id not in cat.by_id:
            raise HTTPException(404, "No comic with that id.")
        return {"results": [{**cat.card(h.index), "similarity": round(h.semantic or 0, 4)}
                            for h in cat.similar(comic_id, limit)]}

    @app.get("/api/ids")
    def ids(request: Request, limit: int = Query(5000, ge=1, le=20000)):
        """Most popular ids, used by the web app to build its sitemap."""
        cat = catalog_of(request)
        idx, _ = cat.browse(Filters(), "popular", limit, 0)
        return {"ids": [cat.records[i]["id"] for i in idx]}

    return app


app = create_app()
