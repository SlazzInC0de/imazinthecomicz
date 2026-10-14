import numpy as np
import pandas as pd

from engine import SemanticMatrixEngine
from vibe import add_vibe_features, scope_score, tone_score


class _StubModel:
    """Returns a fixed query vector so ranking can be tested without downloading a model."""

    def __init__(self, vector):
        self.vector = np.asarray(vector, dtype=float)

    def encode(self, *_args, **_kwargs):
        return self.vector


def _engine(vectors, tones, scopes, query):
    eng = SemanticMatrixEngine.__new__(SemanticMatrixEngine)
    eng._model = _StubModel(query)
    eng.vector_matrix = np.asarray(vectors, dtype=float)
    eng.catalog = pd.DataFrame({
        "Title": [f"T{i}" for i in range(len(vectors))],
        "tone_vector": tones,
        "scope_vector": scopes,
    })
    return eng


def test_tone_and_scope_are_bounded_and_directional():
    assert tone_score("Horror / Thriller", "Mature 17+") > tone_score("Comedy / Slice of Life", "All Ages")
    assert scope_score("Mecha / Sci-Fi") > scope_score("School / Romance")
    for value in (tone_score("Dark Fantasy / Horror", "Mature 17+"), scope_score("Slice of Life / School")):
        assert 0.0 <= value <= 1.0


def test_add_vibe_features_creates_varied_columns():
    catalog = pd.DataFrame({
        "Genre": ["Horror / Supernatural", "Comedy / Slice of Life", "Mecha / Sci-Fi"],
        "Age Rating": ["Mature", "All Ages", "Teen+"],
    })
    out = add_vibe_features(catalog)
    assert out["tone_vector"].nunique() > 1
    assert out["scope_vector"].nunique() > 1
    assert "tone_vector" not in catalog.columns  # input is not mutated


def test_semantic_match_dominates_ranking():
    eng = _engine([[1, 0], [0, 1]], [0.5, 0.5], [0.5, 0.5], query=[1, 0])
    results = eng.search("q", top_k=2, tone=0.5, scope=0.5)
    assert list(results["Title"]) == ["T0", "T1"]


def test_sliders_break_ties_between_equal_semantic_matches():
    eng = _engine([[1, 0], [1, 0]], [0.1, 0.9], [0.5, 0.5], query=[1, 0])
    dark = eng.search("q", top_k=2, tone=1.0, scope=0.5)
    campy = eng.search("q", top_k=2, tone=0.0, scope=0.5)
    assert dark.iloc[0]["Title"] == "T1"
    assert campy.iloc[0]["Title"] == "T0"


def test_slider_penalty_is_capped_at_30_percent():
    eng = _engine([[1, 0]], [0.0], [0.0], query=[1, 0])
    row = eng.search("q", top_k=1, tone=1.0, scope=1.0).iloc[0]
    assert np.isclose(row["semantic_score"], 1.0)
    assert np.isclose(row["composite_score"], 0.7)


def test_init_loads_named_model(monkeypatch):
    import engine as engine_module

    loaded = {}
    monkeypatch.setattr(engine_module, "SentenceTransformer", lambda name: loaded.setdefault("name", name))
    SemanticMatrixEngine(model_name="all-MiniLM-L6-v2")
    assert loaded["name"] == "all-MiniLM-L6-v2"


def test_index_catalog_loads_cached_files(tmp_path):
    catalog = pd.DataFrame({"Title": ["A", "B"], "tone_vector": [0.1, 0.9], "scope_vector": [0.5, 0.5]})
    catalog.to_pickle(tmp_path / "catalog.pkl")
    np.save(tmp_path / "vectors.npy", np.eye(2))

    eng = SemanticMatrixEngine.__new__(SemanticMatrixEngine)
    eng.index_catalog(str(tmp_path / "catalog.pkl"), str(tmp_path / "vectors.npy"))
    assert list(eng.catalog["Title"]) == ["A", "B"]
    assert eng.vector_matrix.shape == (2, 2)


def test_missing_cache_file_names_the_file(tmp_path):
    import pytest

    eng = SemanticMatrixEngine.__new__(SemanticMatrixEngine)
    with pytest.raises(FileNotFoundError, match="nope.pkl"):
        eng.index_catalog(str(tmp_path / "nope.pkl"), str(tmp_path / "nope.npy"))


def test_zero_vectors_do_not_divide_by_zero():
    eng = _engine([[0, 0], [1, 0]], [0.5, 0.5], [0.5, 0.5], query=[1, 0])
    results = eng.search("q", top_k=2)
    assert np.isfinite(results["composite_score"]).all()
    assert results.iloc[0]["Title"] == "T1"
