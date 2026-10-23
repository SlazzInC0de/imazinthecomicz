import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))

from build_dataset import anilist_row, build, comicvine_row  # noqa: E402
from text import clean_description, first_paragraphs  # noqa: E402
from vibe import raw_scores, to_percentiles, western_genres  # noqa: E402

LONG = "A long enough description about a hero who walks through a ruined city looking for answers. " * 2


def media(**over):
    base = {
        "id": 1, "title": {"english": "Night Walker", "romaji": "Yoru no Arukibito", "native": "夜の歩き人"},
        "synonyms": [], "format": "MANGA", "status": "FINISHED", "description": LONG,
        "startDate": {"year": 2011}, "chapters": 90, "volumes": 10, "meanScore": 81, "popularity": 5000,
        "genres": ["Horror", "Drama"],
        "tags": [{"name": "Tragedy", "rank": 90, "isMediaSpoiler": False, "isAdult": False},
                 {"name": "Twist Ending", "rank": 80, "isMediaSpoiler": True, "isAdult": False}],
        "countryOfOrigin": "JP", "coverImage": {"extraLarge": "https://img/x.jpg", "color": "#e4a15d"},
        "siteUrl": "https://anilist.co/manga/1",
        "staff": {"edges": [{"role": "Story & Art", "node": {"name": {"full": "Aki Mori"}}},
                            {"role": "Translator (English)", "node": {"name": {"full": "Someone"}}}]},
    }
    base.update(over)
    return base


def test_clean_description_strips_html_and_source_notes():
    raw = "First line.<br><br>Second <i>line</i> &amp; more.<br>(Source: MangaUpdates)"
    assert clean_description(raw) == "First line.\n\nSecond line & more."


def test_first_paragraphs_cuts_at_boundary():
    text = "Para one is here. " * 30 + "\n\n" + "Para two. " * 100
    out = first_paragraphs(text, limit=700)
    assert len(out) <= 700 and out.endswith(".")


def test_anilist_row_maps_fields_and_hides_spoiler_tags():
    row = anilist_row(media())
    assert row["id"] == "al-1" and row["kind"] == "Manga" and row["status"] == "Completed"
    assert row["creators"] == ["Aki Mori"]
    assert row["tags"] == ["Tragedy"]
    assert "Yoru no Arukibito" in row["alt_titles"]


def test_anilist_row_drops_novels_short_text_and_unreleased():
    assert anilist_row(media(format="NOVEL")) is None
    assert anilist_row(media(description="Too short.")) is None
    assert anilist_row(media(status="NOT_YET_RELEASED")) is None


def test_country_decides_kind():
    assert anilist_row(media(countryOfOrigin="KR"))["kind"] == "Manhwa"
    assert anilist_row(media(countryOfOrigin="CN"))["kind"] == "Manhua"


def test_comicvine_row_and_genres_from_text():
    vol = {"id": 7, "name": "Gotham Nights", "deck": "Batman hunts a murderer through the city.",
           "description": "<p>A noir crime story where the detective vigilante faces a serial killer.</p>" * 2,
           "start_year": "1999", "publisher": {"name": "DC Comics"}, "count_of_issues": 24,
           "image": {"super_url": "https://img/cv.jpg"}, "site_detail_url": "https://comicvine/7"}
    row = comicvine_row(vol)
    assert row["id"] == "cv-7" and row["year"] == 1999 and row["publisher"] == "DC Comics"
    assert "Crime" in row["genres"] and "Superhero" in row["genres"]


def test_western_genres_counts_matches():
    assert western_genres("Aliens invade the galaxy on a starship") == ["Sci-Fi"]


def test_vibe_direction():
    dark, _ = raw_scores(["Horror"], [{"name": "Gore", "rank": 100}])
    light, _ = raw_scores(["Comedy"], [{"name": "Iyashikei", "rank": 100}])
    _, epic = raw_scores(["Sci-Fi"], [{"name": "Space", "rank": 100}])
    _, small = raw_scores(["Slice of Life"], [{"name": "School", "rank": 100}])
    assert dark > 0 > light and epic > 0 > small


def test_percentiles_are_bounded_and_ties_equal():
    out = to_percentiles([3.0, 1.0, 1.0, 2.0])
    assert out.min() >= 0 and out.max() == 1.0 and out[1] == out[2]


def test_build_merges_sources_and_adds_doc():
    vol = {"id": 9, "name": "Star Rangers", "deck": "", "description": "Space rangers patrol the galaxy. " * 6,
           "start_year": "1985", "publisher": {"name": "Image"}, "count_of_issues": 40, "image": {},
           "site_detail_url": "u"}
    df = build([media(), media(id=2, title={"english": "Sunny Days"}, genres=["Comedy"], tags=[])], [vol])
    assert len(df) == 3
    assert set(df["source"]) == {"AniList", "Comic Vine"}
    assert df["tone"].between(0, 1).all() and df["scope"].between(0, 1).all()
    night = df[df["id"] == "al-1"].iloc[0]
    assert night["doc"].startswith("Night Walker") and "Themes: Tragedy" in night["doc"]
    assert np.isclose(df.loc[df["id"] == "al-1", "tone"].iloc[0], 1.0)


def test_anilist_walks_past_the_5000_cap(tmp_path, monkeypatch):
    import gzip
    import json

    import fetch_anilist

    # 12,000 fake titles, popularity falling with plenty of ties
    items = [{"id": i, "popularity": 20000 - i // 7} for i in range(12000)]

    def fake_page(session, page, per_page, below):
        pool = [m for m in items if below is None or m["popularity"] < below]
        if page * per_page > 5000:
            raise RuntimeError("AniList refuses pages past 5000 results")
        chunk = pool[(page - 1) * per_page: page * per_page]
        return {"media": chunk, "pageInfo": {"hasNextPage": page * per_page < len(pool)}}

    out = tmp_path / "a.jsonl.gz"
    monkeypatch.setattr(fetch_anilist, "fetch_page", fake_page)
    monkeypatch.setattr(fetch_anilist.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["x", "--max", "11000", "--out", str(out)])
    assert fetch_anilist.main() == 0
    ids = [json.loads(line)["id"] for line in gzip.open(out, "rt")]
    assert len(ids) == len(set(ids)) >= 11000
    assert ids[:11000] == list(range(11000))


def test_metron_row_maps_genres_and_status():
    from build_dataset import metron_row

    series = {"id": 42, "name": "Saga", "desc": "An epic space opera about two soldiers from warring alien races "
              "who fall in love and go on the run with their newborn daughter across the galaxy.",
              "year_began": 2012, "year_end": None, "issue_count": 66, "series_type": {"name": "Ongoing Series"},
              "publisher": {"name": "Image"}, "genres": [{"name": "Science Fiction"}, {"name": "Romance"}],
              "cover": "https://static.metron.cloud/x.jpg", "resource_url": "https://metron.cloud/series/saga/"}
    row = metron_row(series)
    assert row["id"] == "mt-42" and row["kind"] == "Western" and row["status"] == "Ongoing"
    assert row["genres"][:2] == ["Sci-Fi", "Romance"] and row["length"] == 66
    assert metron_row({**series, "desc": "short"}) is None
    df = build([], [], [series])
    assert df.iloc[0]["source"] == "Metron"
