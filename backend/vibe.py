"""Tone (campy -> grimdark) and scope (street-level -> cosmic) features.

Scores live in [0, 1] and come from genres + tags, which on AniList are
crowd-voted, so the sliders work on real signal.
"""
TONE_WEIGHTS = {
    "horror": 0.3, "psychological": 0.25, "gore": 0.3, "tragedy": 0.25, "dark fantasy": 0.25,
    "thriller": 0.15, "noir": 0.2, "crime": 0.15, "war": 0.2, "revenge": 0.15, "survival": 0.15,
    "death game": 0.2, "seinen": 0.1, "drama": 0.05, "mystery": 0.05, "post-apocalyptic": 0.15,
    "comedy": -0.25, "parody": -0.25, "gag humor": -0.3, "slice of life": -0.2, "iyashikei": -0.3,
    "romance": -0.1, "romantic comedy": -0.2, "school": -0.1, "sports": -0.1, "cute girls doing cute things": -0.3,
    "kids": -0.25, "humor": -0.25, "family": -0.1,
}

SCOPE_WEIGHTS = {
    "sci-fi": 0.25, "space": 0.3, "mecha": 0.3, "aliens": 0.25, "gods": 0.3, "mythology": 0.25,
    "isekai": 0.25, "fantasy": 0.2, "supernatural": 0.15, "cosmic": 0.35, "time manipulation": 0.15,
    "super power": 0.15, "superhero": 0.15, "adventure": 0.1, "post-apocalyptic": 0.15, "war": 0.1,
    "slice of life": -0.3, "school": -0.2, "workplace": -0.2, "crime": -0.15, "noir": -0.2,
    "sports": -0.2, "romance": -0.15, "urban": -0.15, "detective": -0.15, "cooking": -0.25,
    "music": -0.15, "martial arts": -0.05, "historical": -0.05,
}


def _score(labels: list[str], weights: dict) -> float:
    text = " | ".join(l.lower() for l in labels if l)
    raw = 0.5 + sum(w for key, w in weights.items() if key in text)
    return float(min(max(raw, 0.0), 1.0))


def tone_score(genres: list[str], tags: list[str]) -> float:
    return _score(genres + tags, TONE_WEIGHTS)


def scope_score(genres: list[str], tags: list[str]) -> float:
    return _score(genres + tags, SCOPE_WEIGHTS)
