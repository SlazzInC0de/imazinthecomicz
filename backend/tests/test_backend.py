import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.build_index import build, build_catalog
from backend.embedder import HashingEmbedder
from backend.engine import SearchEngine
from backend.normalize import clean_text, from_anilist, from_metron
from backend.vibe import scope_score, tone_score

ANILIST = [
    {
        "id": 30013, "siteUrl": "https://anilist.co/manga/30013",
        "title": {"english": "One Piece", "romaji": "ONE PIECE"},
        "description": "Pirate Luffy sails the Grand Line hunting for treasure.<br>(Source: Viz)",
        "format": "MANGA", "status": "RELEASING", "countryOfOrigin": "JP", "chapters": None, "volumes": None,
        "averageScore": 88, "popularity": 500, "startDate": {"year": 1997},
        "genres": ["Action", "Adventure", "Comedy"],
        "tags": [{"name": "Pirates", "rank": 95, "isMediaSpoiler": False}, {"name": "Secret", "rank": 90, "isMediaSpoiler": True}],
        "coverImage": {"large": "https://img/op.jpg", "color": "#e4a15d"},
        "staff": {"edges": [{"role": "Story & Art", "node": {"name": {"full": "Eiichiro Oda"}}}]},
    },
    {
        "id": 30002, "siteUrl": "https://anilist.co/manga/30002",
        "title": {"english": None, "romaji": "Berserk"},
        "description": "A lone mercenary swordsman fights demons in a grim medieval world full of horror.",
        "format": "MANGA", "status": "RELEASING", "countryOfOrigin": "JP", "chapters": None, "volumes": None,
        "averageScore": 93, "popularity": 300, "startDate": {"year": 1989},
        "genres": ["Action", "Drama", "Fantasy", "Horror", "Psychological"],
        "tags": [{"name": "Gore", "rank": 90, "isMediaSpoiler": False}],
        "coverImage": {"large": "https://img/b.jpg", "color": None}, "staff": {"edges": []},
    },
    {
        "id": 105398, "siteUrl": "https://anilist.co/manga/105398",
        "title": {"english": "Solo Leveling", "romaji": "Na Honjaman Level Up"},
        "description": "A weak hunter gains a system that lets him level up alone through dungeons.",
        "format": "MANGA", "status": "FINISHED", "countryOfOrigin": "KR", "chapters": 201, "volumes": 14,
        "averageScore": 85, "popularity": 400, "startDate": {"year": 2018},
        "genres": ["Action", "Fantasy"], "tags": [], "coverImage": {"large": None, "color": None}, "staff": {"edges": []},
    },
]
METRON = [
    {
        "id": 1, "name": "Daredevil", "year_began": 1964, "year_end": 1998, "issue_count": 380, "volume": 1,
        "desc": "A blind lawyer fights crime in Hell's Kitchen as a masked vigilante.",
        "publisher": {"id": 1, "name": "Marvel"}, "series_type": {"id": 1, "name": "Ongoing Series"},
        "genres": [{"id": 1, "name": "Super-Hero"}, {"id": 2, "name": "Crime"}],
    }
]


@pytest.fixture()
def raw_dir(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "anilist.jsonl").write_text("\n".join(json.dumps(m) for m in ANILIST))
    (raw / "metron.jsonl").write_text("\n".join(json.dumps(s) for s in METRON))
    return raw


@pytest.fixture()
def engine(raw_dir, tmp_path):
    build(raw_dir, tmp_path / "out", embedder=HashingEmbedder())
    return SearchEngine.load(tmp_path / "out")


def test_clean_text_strips_html_and_source():
    assert clean_text("Hi<br>there <i>x</i> (Source: Viz)") == "Hi there x"


def test_from_anilist_maps_fields():
    c = from_anilist(ANILIST[0])
    assert c["id"] == "al-30013" and c["kind"] == "Manga" and c["score"] == 8.8
    assert c["tags"] == ["Pirates"]  # spoiler tag dropped
    assert c["creators"] == ["Eiichiro Oda (Story & Art)"]
    assert from_anilist(ANILIST[1])["title"] == "Berserk"
    assert from_anilist(ANILIST[2])["kind"] == "Manhwa"


def test_from_metron_maps_fields():
    c = from_metron(METRON[0])
    assert c["id"] == "mt-1" and c["kind"] == "Western" and c["publisher"] == "Marvel"
    assert c["status"] == "Finished" and c["genres"] == ["Super-Hero", "Crime"]


def test_vibe_scores_are_bounded_and_ordered():
    dark = tone_score(["Horror", "Psychological"], ["Gore"])
    light = tone_score(["Comedy", "Slice of Life"], [])
    assert 0 <= light < dark <= 1
    assert scope_score(["Sci-Fi", "Mecha"], ["Space"]) > scope_score(["Slice of Life"], ["School"])


def test_build_catalog_merges_sources(raw_dir):
    cat = build_catalog(raw_dir)
    assert {c["source"] for c in cat} == {"anilist", "metron"}
    assert all("doc" in c and 0 <= c["tone"] <= 1 for c in cat)


def test_search_ranks_meaning(engine):
    res = engine.search("blind lawyer fights crime", k=3)
    assert res[0]["title"] == "Daredevil"


def test_search_kind_filter(engine):
    res = engine.search("hunter dungeons level up", kind="Manga", k=5)
    assert all(r["kind"] == "Manga" for r in res)


def test_tone_slider_reorders(engine):
    def berserk(tone):
        return next(r for r in engine.search("swordsman demons", tone=tone, k=4) if r["id"] == "al-30002")
    assert berserk(1.0)["score_composite"] > berserk(0.0)["score_composite"]


def test_similar_and_trending(engine):
    sim = engine.similar("al-30002", k=2)
    assert len(sim) == 2 and all(s["id"] != "al-30002" for s in sim)
    assert engine.trending(k=1)[0]["title"] == "One Piece"


def test_api(engine, monkeypatch):
    app_module.app.dependency_overrides[app_module.get_engine] = lambda: engine
    client = TestClient(app_module.app)
    try:
        assert client.get("/api/health").status_code == 200
        r = client.get("/api/search", params={"q": "pirate treasure", "k": 2})
        assert r.status_code == 200 and r.json()["results"][0]["title"] == "One Piece"
        assert client.get("/api/comics/al-30013").json()["title"] == "One Piece"
        assert client.get("/api/comics/nope").status_code == 404
        assert client.get("/api/comics/al-30013/similar").status_code == 200
        assert client.get("/api/stats").json()["total"] == 4
        assert client.get("/api/search", params={"q": "x"}).status_code == 422
    finally:
        app_module.app.dependency_overrides.clear()
