"""
Tone (lighter -> darker) and scope (grounded -> epic) for every title.

AniList attaches ranked tags to each title ("Tragedy 87%", "Iyashikei 92%").
Each known tag and genre pushes the score one way, weighted by its rank. The
raw sums are then turned into percentiles, so 0.5 always means "middle of the
catalog" and the sliders spread results evenly instead of bunching up.
"""
import re

import numpy as np

TONE_GENRES = {
    "Horror": 0.5, "Psychological": 0.4, "Thriller": 0.35, "Drama": 0.15, "Mystery": 0.1,
    "Crime": 0.2, "War": 0.35,
    "Comedy": -0.45, "Slice of Life": -0.35, "Romance": -0.15, "Sports": -0.15,
    "Music": -0.15, "Mahou Shoujo": -0.1, "Ecchi": -0.1,
}
TONE_TAGS = {
    "Tragedy": 0.5, "Gore": 0.6, "Body Horror": 0.6, "Cosmic Horror": 0.55, "Death Game": 0.5,
    "Torture": 0.6, "Revenge": 0.35, "Dystopian": 0.35, "Post-Apocalyptic": 0.35, "War": 0.4,
    "Survival": 0.3, "Anti-Hero": 0.25, "Organized Crime": 0.3, "Crime": 0.2, "Zombie": 0.4,
    "Vampire": 0.15, "Villainess": 0.05, "Psychological": 0.3, "Bullying": 0.3, "Terrorism": 0.4,
    "Iyashikei": -0.6, "Slapstick": -0.5, "Parody": -0.4, "Surreal Comedy": -0.4,
    "Cute Girls Doing Cute Things": -0.6, "Cute Boys Doing Cute Things": -0.5, "Cooking": -0.3,
    "Food": -0.3, "Family Life": -0.25, "School Club": -0.2, "Animals": -0.2, "Episodic": -0.1,
    "Heterosexual": -0.05, "Romantic Subtext": -0.05, "Gag Humor": -0.5,
}
SCOPE_GENRES = {
    "Sci-Fi": 0.3, "Fantasy": 0.25, "Mecha": 0.35, "Supernatural": 0.15, "Adventure": 0.15,
    "Superhero": 0.15,
    "Slice of Life": -0.35, "Romance": -0.15, "Sports": -0.2, "Music": -0.15, "Mystery": -0.1,
    "Crime": -0.25,
}
SCOPE_TAGS = {
    "Space": 0.5, "Aliens": 0.4, "Gods": 0.5, "Mythology": 0.4, "Isekai": 0.3, "Dragons": 0.25,
    "Kingdom Management": 0.3, "War": 0.3, "Post-Apocalyptic": 0.3, "Dystopian": 0.2,
    "Super Power": 0.2, "Magic": 0.15, "Cultivation": 0.35, "Time Manipulation": 0.2,
    "Military": 0.2, "Royal Affairs": 0.15, "Space Opera": 0.5, "Apocalypse": 0.4,
    "School": -0.3, "Workplace": -0.35, "Office Lady": -0.35, "Urban": -0.2, "Rural": -0.25,
    "Family Life": -0.3, "Detective": -0.25, "Organized Crime": -0.15, "Delinquents": -0.25,
    "Coming of Age": -0.15, "Cooking": -0.35, "Food": -0.35, "Martial Arts": -0.05,
}

# Comic Vine has no tags, so Western series get genre words from their description.
WESTERN_GENRES = [
    ("Superhero", r"\bsuper[- ]?heroe?s?\b|\bsuper[- ]?powers?\b|\bmutants?\b|\bavengers\b|\bx-men\b|"
                  r"\bjustice league\b|\bbatman\b|\bsuperman\b|\bspider-man\b|\bwonder woman\b|\bvigilante\b"),
    ("Horror", r"\bhorror\b|\bzombies?\b|\bvampires?\b|\bdemons?\b|\bhaunted\b|\bmonsters?\b|\bterror\b"),
    ("Sci-Fi", r"\bscience fiction\b|\bsci-fi\b|\baliens?\b|\bgalaxy\b|\bgalactic\b|\brobots?\b|\bcyborgs?\b|"
               r"\bstarship\b|\bspace\b|\bplanets?\b"),
    ("Fantasy", r"\bfantasy\b|\bmagic\b|\bwizards?\b|\bsorcer|\bdragons?\b|\bkingdom\b|\bquest\b"),
    ("Crime", r"\bcrime\b|\bdetective\b|\bnoir\b|\bgangsters?\b|\bmobsters?\b|\bheist\b|\bmurders?\b|\bcops?\b"),
    ("War", r"\bwar\b|\bsoldiers?\b|\bmilitary\b|\bbattlefield\b"),
    ("Comedy", r"\bcomedy\b|\bhumou?r\b|\bfunny\b|\bparody\b|\bsatire\b|\bgags?\b"),
    ("Romance", r"\bromance\b|\blove story\b|\bromantic\b"),
    ("Western", r"\bcowboys?\b|\bgunslingers?\b|\bwild west\b|\bthe frontier\b"),
    ("Adventure", r"\badventures?\b|\bexplor"),
    ("Drama", r"\bdrama\b|\bcoming[- ]of[- ]age\b"),
]
_WESTERN = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in WESTERN_GENRES]


def western_genres(text: str, limit: int = 4) -> list[str]:
    hits = []
    for name, pattern in _WESTERN:
        count = len(pattern.findall(text))
        if count:
            hits.append((count, name))
    hits.sort(key=lambda pair: -pair[0])
    return [name for _, name in hits[:limit]]


def raw_scores(genres: list[str], tags: list[dict]) -> tuple[float, float]:
    tone = sum(TONE_GENRES.get(g, 0.0) for g in genres)
    scope = sum(SCOPE_GENRES.get(g, 0.0) for g in genres)
    for tag in tags:
        weight = (tag.get("rank") or 0) / 100.0
        tone += TONE_TAGS.get(tag["name"], 0.0) * weight
        scope += SCOPE_TAGS.get(tag["name"], 0.0) * weight
    return tone, scope


def to_percentiles(values) -> np.ndarray:
    """Rank-based scaling to [0, 1]; ties share the average rank."""
    arr = np.asarray(values, dtype=float)
    if len(arr) < 2:
        return np.full(len(arr), 0.5)
    order = arr.argsort(kind="mergesort")
    ranks = np.empty(len(arr))
    ranks[order] = np.arange(len(arr))
    # average ranks of ties so identical raw scores land on the same value
    _, inverse, counts = np.unique(arr, return_inverse=True, return_counts=True)
    sums = np.bincount(inverse, weights=ranks)
    return (sums / counts)[inverse] / (len(arr) - 1)
