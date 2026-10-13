"""
Derive the tone (campy -> grimdark) and scope (street -> cosmic) features
that the Vibe Control sliders rank against.

Both scores live in [0, 1] and are computed from catalog metadata, so the
sliders have real signal to work with instead of a constant placeholder.
"""
import pandas as pd

# Genre keyword -> tone contribution (positive = darker)
TONE_WEIGHTS = {
    "horror": 0.35, "dark fantasy": 0.35, "psychological": 0.3, "noir": 0.3,
    "crime": 0.2, "thriller": 0.2, "war": 0.2, "political": 0.1, "seinen": 0.1,
    "historical": 0.05, "mystery": 0.05, "drama": 0.05,
    "comedy": -0.3, "slice of life": -0.2, "romance": -0.15, "gaming": -0.15,
    "music": -0.1, "sports": -0.1, "school": -0.1, "coming of age": -0.05,
}

AGE_TONE = {
    "All Ages": -0.2, "Teen+": 0.0, "Young Adult": 0.05,
    "Mature": 0.15, "Mature 17+": 0.2,
}

# Genre keyword -> scope contribution (positive = more cosmic)
SCOPE_WEIGHTS = {
    "sci-fi": 0.35, "mecha": 0.35, "mythology": 0.3, "isekai": 0.3,
    "fantasy": 0.25, "supernatural": 0.2, "superhero": 0.1, "adventure": 0.1,
    "slice of life": -0.3, "school": -0.25, "crime": -0.2, "noir": -0.2,
    "sports": -0.2, "romance": -0.15, "literary": -0.15, "music": -0.15,
    "martial arts": -0.1, "historical": -0.1, "drama": -0.05,
}


def _keyword_score(genre: str, weights: dict) -> float:
    text = str(genre).lower()
    return sum(w for key, w in weights.items() if key in text)


def tone_score(genre: str, age_rating: str) -> float:
    raw = 0.5 + _keyword_score(genre, TONE_WEIGHTS) + AGE_TONE.get(str(age_rating), 0.0)
    return float(min(max(raw, 0.0), 1.0))


def scope_score(genre: str) -> float:
    raw = 0.5 + _keyword_score(genre, SCOPE_WEIGHTS)
    return float(min(max(raw, 0.0), 1.0))


def add_vibe_features(catalog: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the catalog with tone_vector and scope_vector columns."""
    out = catalog.copy()
    genre = out.get("Genre", pd.Series("", index=out.index))
    age = out.get("Age Rating", pd.Series("", index=out.index))
    out["tone_vector"] = [tone_score(g, a) for g, a in zip(genre, age)]
    out["scope_vector"] = [scope_score(g) for g in genre]
    return out
