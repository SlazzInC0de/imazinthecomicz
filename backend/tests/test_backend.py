import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.build_index import build, build_catalog
from backend.embedder import HashingEmbedder
from backend.engine import SearchEngine
from backend.normalize import clean_text, from_anilist, from_metron, is_comic_page, western_kind
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
SPIDEY = [
    {"id": 20, "name": "The Amazing Spider-Man", "year_began": 1963, "issue_count": 900, "volume": 1, "desc": "",
     "publisher": {"id": 1, "name": "Marvel"}, "series_type": None, "genres": [{"id": 1, "name": "Super-Hero"}]},
    {"id": 21, "name": "Spider-Man 2099", "year_began": 1992, "issue_count": 46, "volume": 1, "desc": "",
     "publisher": {"id": 1, "name": "Marvel"}, "series_type": None, "genres": [{"id": 1, "name": "Super-Hero"}]},
    {"id": 22, "name": "Batman", "year_began": 1940, "issue_count": 713, "volume": 1, "desc": "",
     "publisher": {"id": 2, "name": "DC Comics"}, "series_type": None, "genres": [{"id": 1, "name": "Super-Hero"}]},
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
    assert c["id"] == "mt-1" and c["kind"] == "Marvel" and c["publisher"] == "Marvel"
    assert c["status"] == "Finished" and c["genres"] == ["Super-Hero", "Crime"]


def test_western_kind_split():
    assert western_kind("Marvel") == "Marvel"
    assert western_kind("DC Comics") == "DC"
    assert western_kind("Image") == "Western"
    assert western_kind("Dark Horse Comics") == "Western"
    assert western_kind(None) == "Western"


def test_pick_series_ranks_by_issue_count_per_bucket():
    from backend.ingest.metron import pick_series
    index = [
        {"id": 1, "issue_count": 900, "publisher": {"name": "Marvel"}},
        {"id": 2, "issue_count": 50, "publisher": {"name": "Marvel"}},
        {"id": 3, "issue_count": 1000, "publisher": {"name": "DC Comics"}},
        {"id": 4, "issue_count": 300, "publisher": {"name": "Image"}},
        {"id": 5, "issue_count": 1, "publisher": {"name": "Image"}},
    ]
    picked = pick_series(index, marvel=1, dc=5, others=5, min_issues=3)
    assert [s["id"] for s in picked] == [1, 3, 4]


def test_same_title_different_years_are_kept(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    vol1 = {**METRON[0], "id": 10, "year_began": 1964}
    vol2 = {**METRON[0], "id": 11, "year_began": 2016, "volume": 6}
    (raw / "metron.jsonl").write_text(json.dumps(vol1) + "\n" + json.dumps(vol2))
    assert len(build_catalog(raw)) == 2


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
        assert client.get("/api/search", params={"q": "lawyer", "kind": "Marvel"}).json()["results"][0]["title"] == "Daredevil"
        r = client.get("/api/search", params={"q": "pirate treasure", "k": 2})
        assert r.status_code == 200 and r.json()["results"][0]["title"] == "One Piece"
        assert client.get("/api/comics/al-30013").json()["title"] == "One Piece"
        assert client.get("/api/comics/nope").status_code == 404
        assert client.get("/api/comics/al-30013/similar").status_code == 200
        assert client.get("/api/stats").json()["total"] == 4
        assert client.get("/api/search", params={"q": "x"}).status_code == 422
    finally:
        app_module.app.dependency_overrides.clear()


def test_alias_expansion():
    from backend.aliases import expand, normalize
    assert expand("web swinger") == ["Spider-Man"]
    assert expand("the Dark Knight in Gotham") == ["Batman", "Gotham"]
    assert expand("a quiet cooking story") == []
    assert normalize("The Amazing Spider-Man!") == "the amazing spiderman"


@pytest.fixture()
def hero_engine(raw_dir, tmp_path):
    with (raw_dir / "metron.jsonl").open("a") as fh:
        fh.write("\n" + "\n".join(json.dumps(s) for s in SPIDEY))
    build(raw_dir, tmp_path / "heroes", embedder=HashingEmbedder())
    return SearchEngine.load(tmp_path / "heroes")


def test_nickname_finds_spider_man(hero_engine):
    res = hero_engine.search("web swinger", k=3)
    assert res[0]["title"] == "The Amazing Spider-Man"  # popular flagship beats Spider-Man 2099
    assert res[1]["title"] == "Spider-Man 2099"


def test_title_typed_without_hyphen(hero_engine):
    assert hero_engine.search("spiderman", k=1)[0]["title"] == "The Amazing Spider-Man"
    assert hero_engine.search("dark knight", k=1)[0]["title"] == "Batman"


def test_wiki_extract_fills_missing_description(raw_dir):
    with (raw_dir / "metron.jsonl").open("a") as fh:
        fh.write("\n" + json.dumps(SPIDEY[0]))
    (raw_dir / "wiki.jsonl").write_text(json.dumps({"id": "mt-20", "wiki_extract": "The Amazing Spider-Man is a comic book series. Peter Parker swings across New York.", "wiki_url": "https://en.wikipedia.org/wiki/The_Amazing_Spider-Man"}))
    c = next(c for c in build_catalog(raw_dir) if c["id"] == "mt-20")
    assert c["description"].endswith("Peter Parker swings across New York.")
    assert "Peter Parker" in c["doc"] and c["wiki_url"].endswith("Spider-Man")


def test_wiki_lookup_rejects_unrelated_page():
    import httpx
    from backend.ingest import wiki
    c = {"title": "The Amazing Spider-Man", "kind": "Marvel", "publisher": "Marvel", "description": ""}

    def handler(request):
        title = "The Amazing Spider-Man" if "Spider" in str(request.url) else "Unrelated"
        return httpx.Response(200, json={"query": {"pages": {"1": {"title": title, "extract": "The Amazing Spider-Man is an American comic book series.", "fullurl": "u"}}}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert wiki.lookup(client, c)["wiki_title"] == "The Amazing Spider-Man"
        assert wiki.lookup(client, {**c, "title": "Zzz"}) is None


@pytest.mark.parametrize("title, extract, ok", [
    ("Iron Man (comic book)", "Iron Man is a comic book series published by Marvel Comics.", True),
    ("Whisper Me a Love Song", "Whisper Me a Love Song is a Japanese manga series by Eku Takeshima.", True),
    ("Eerie (magazine)", "Eerie is an American magazine of horror comics introduced in 1966.", True),
    ("Spider-Man: Homecoming", "Spider-Man: Homecoming is a 2017 American superhero film based on the Marvel Comics character.", False),
    ("Death Note (2006 TV series)", "Death Note is a Japanese anime television series based on the manga.", False),
    ("Among Us", "Among Us is a 2018 online multiplayer social deduction game.", False),
    ("20th Century Studios", "20th Century Studios, Inc. is an American film production company.", False),
])
def test_wiki_page_must_be_about_the_comic(title, extract, ok):
    assert is_comic_page(title, extract) is ok


def test_build_catalog_drops_film_pages(raw_dir):
    (raw_dir / "wiki.jsonl").write_text(json.dumps({"id": "mt-1", "wiki_title": "Some Film", "wiki_extract": "Some Film is a 2017 American superhero film."}))
    assert all(c["wiki_extract"] is None for c in build_catalog(raw_dir))


def test_daily_pick_and_random(engine):
    a, b = engine.daily_pick(1), engine.daily_pick(1)
    assert a["id"] == b["id"] and a["cover"]
    assert engine.random(np.random.default_rng(0), "Manhwa")["kind"] == "Manhwa"


def test_pick_and_random_api(engine):
    app_module.app.dependency_overrides[app_module.get_engine] = lambda: engine
    try:
        client = TestClient(app_module.app)
        assert client.get("/api/pick").json()["id"]
        assert client.get("/api/random", params={"kind": "Marvel"}).json()["kind"] == "Marvel"
    finally:
        app_module.app.dependency_overrides.clear()


def test_unrelated_query_returns_nothing(engine):
    assert engine.search("zzqx qwvv", k=5) == []
