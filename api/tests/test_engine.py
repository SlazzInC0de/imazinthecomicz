from app.engine import BM25, Filters, tokenize


def ids(catalog, hits):
    return [catalog.records[h.index]["id"] for h in hits]


def test_tokenize_drops_stopwords_and_punctuation():
    assert tokenize("The Ghost-Detective of Tokyo!") == ["ghost", "detective", "tokyo"]


def test_bm25_prefers_rarer_terms():
    bm = BM25([["ghost", "city"], ["city", "city"], ["dragon"]])
    scores = bm.score(["ghost", "city"])
    assert scores[0] > scores[1] > scores[2] == 0


def test_semantic_query_finds_meaning(frame):
    """Query shares no words with any title, so only the embedding can find it."""
    import numpy as np

    from app.engine import Catalog

    target = frame.index[frame["id"] == "al-3"][0]
    vectors = np.eye(len(frame), dtype=np.float32)

    class Stub:
        def embed_query(self, text):
            return vectors[target]

    cat = Catalog(frame, vectors, Stub(), {})
    hits, _ = cat.search("zxqv wplk", Filters())
    assert ids(cat, hits)[0] == "al-3"
    assert hits[0].keyword == 0


def test_exact_title_wins(catalog):
    hits, _ = catalog.search("Bakery Days", Filters())
    assert ids(catalog, hits)[0] == "al-4"


def test_filters_restrict_results(catalog):
    hits, total = catalog.search("adventure", Filters(kinds=["Manhua"]))
    assert ids(catalog, hits) == ["al-6"] and total == 1
    hits, _ = catalog.search("story", Filters(genres=["Mystery", "Supernatural"], year_min=2012))
    assert ids(catalog, hits) == ["al-2"]
    hits, _ = catalog.search("city", Filters(status="Ongoing", min_score=80))
    assert ids(catalog, hits) == ["al-5"]


def test_vibe_sliders_reorder(catalog):
    q = "friends fight in a town"
    dark, _ = catalog.search(q, Filters(), tone=1.0)
    light, _ = catalog.search(q, Filters(), tone=0.0)
    score = lambda hits, cid: next(h.score for h in hits if catalog.records[h.index]["id"] == cid)  # noqa: E731
    assert score(dark, "al-5") > score(light, "al-5")
    assert score(light, "al-4") > score(dark, "al-4")
    neutral, _ = catalog.search(q, Filters())
    assert score(neutral, "al-5") >= score(dark, "al-5")


def test_scope_slider_reorders(catalog):
    q = "friends fight in a town"
    epic, _ = catalog.search(q, Filters(), scope=1.0)
    small, _ = catalog.search(q, Filters(), scope=0.0)
    score = lambda hits, cid: next(h.score for h in hits if catalog.records[h.index]["id"] == cid)  # noqa: E731
    assert score(epic, "al-3") > score(small, "al-3")  # space opera
    assert score(small, "al-4") > score(epic, "al-4")  # small-town bakery


def test_missing_year_and_score_load(frame):
    from app.engine import Catalog

    broken = frame.copy()
    broken.loc[0, "year"] = None
    broken.loc[1, "score"] = None
    cat = Catalog(broken, None, None, {})
    assert cat.facets()["total"] == len(frame)
    hits, _ = cat.search("bakery", Filters(year_min=2000))
    assert all(cat.records[h.index]["year"] for h in hits)


def test_stopword_title_still_found_in_keyword_mode(frame):
    from app.engine import Catalog

    renamed = frame.copy()
    renamed.loc[renamed["id"] == "al-4", "title"] = "It Is"
    cat = Catalog(renamed, None, None, {})
    hits, _ = cat.search("it is", Filters())
    assert ids(cat, hits)[0] == "al-4"


def test_similar_fills_the_limit(catalog):
    assert len(catalog.similar("al-3", 4)) == 4


def test_matched_labels(catalog):
    hits, _ = catalog.search("horror survival", Filters())
    top = hits[0]
    assert catalog.records[top.index]["id"] == "al-5"
    assert set(top.matched) >= {"Horror", "Survival"}


def test_keyword_fallback_only_returns_keyword_hits(keyword_catalog):
    assert keyword_catalog.mode == "keyword"
    hits, total = keyword_catalog.search("dragons", Filters())
    assert ids(keyword_catalog, hits) == ["al-6"] and total == 1
    hits, total = keyword_catalog.search("zzzz", Filters())
    assert hits == [] and total == 0


def test_similar_skips_self_and_sequels(catalog):
    sims = ids(catalog, catalog.similar("al-1", 3))
    assert "al-1" not in sims and "al-2" not in sims


def test_browse_sorts(catalog):
    top, total = catalog.browse(Filters(), "popular", 2)
    assert [catalog.records[i]["id"] for i in top] == ["al-1", "al-3"] and total == 6
    newest, _ = catalog.browse(Filters(), "newest", 1)
    assert catalog.records[newest[0]]["id"] == "al-6"
    best, _ = catalog.browse(Filters(), "score", 1)
    assert catalog.records[best[0]]["id"] == "al-5"


def test_card_is_json_safe(catalog):
    card = catalog.card(0)
    assert isinstance(card["genres"], list) and card["publisher"] is None
    assert len(card["blurb"]) <= 241


def test_facets(catalog):
    f = catalog.facets()
    assert f["total"] == 6 and f["kinds"]["Manga"] == 4 and f["mode"] == "hybrid"
    assert f["year_min"] == 2010 and f["year_max"] == 2020
