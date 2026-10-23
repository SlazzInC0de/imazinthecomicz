import os
import sys
import zlib

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))

from app.engine import Catalog, tokenize  # noqa: E402
from build_dataset import build  # noqa: E402

DIM = 256


class HashEmbedder:
    """Bag-of-words hashed into a vector: shared words mean similar vectors,
    which is all the ranking tests need, and no model download."""

    model_name = "hash"

    def vec(self, text: str) -> np.ndarray:
        v = np.zeros(DIM, dtype=np.float32)
        for tok in tokenize(text):
            v[zlib.crc32(tok.encode()) % DIM] += 1
        return v / max(np.linalg.norm(v), 1e-9)

    def embed_query(self, text: str) -> np.ndarray:
        return self.vec(text)


def media(i, title, desc, genres, tags=(), country="JP", pop=1000, year=2010, status="FINISHED", score=70):
    return {
        "id": i, "title": {"english": title, "romaji": None, "native": None}, "synonyms": [], "format": "MANGA",
        "status": status, "description": desc * 3, "startDate": {"year": year}, "chapters": 50, "volumes": 5,
        "meanScore": score, "popularity": pop, "genres": list(genres),
        "tags": [{"name": t, "rank": 90, "isMediaSpoiler": False, "isAdult": False} for t in tags],
        "countryOfOrigin": country, "coverImage": {"extraLarge": f"https://img/{i}.jpg", "color": "#334455"},
        "siteUrl": f"https://anilist.co/manga/{i}", "staff": {"edges": []},
    }


RAW = [
    media(1, "Ghost Detective", "A detective who can see ghosts solves murders in old Tokyo. ", ["Mystery", "Supernatural"],
          ["Detective", "Ghost"], pop=9000),
    media(2, "Ghost Detective 2", "The detective who sees ghosts returns to solve more murders in Tokyo. ",
          ["Mystery", "Supernatural"], ["Detective", "Ghost"], pop=3000, year=2015),
    media(3, "Star Fleet Academy", "Cadets train to pilot starships across the galaxy and fight alien empires. ",
          ["Sci-Fi", "Action"], ["Space", "Aliens"], pop=8000, country="KR"),
    media(4, "Bakery Days", "A cheerful girl opens a small bakery and makes friends in a quiet town. ",
          ["Slice of Life", "Comedy"], ["Iyashikei", "Cooking"], pop=5000),
    media(5, "Blood Harvest", "Survivors fight monsters and each other as a plague turns the city to ruins. ",
          ["Horror", "Drama"], ["Gore", "Survival", "Tragedy"], pop=7000, status="RELEASING", score=85),
    media(6, "Dragon Throne", "A young mage climbs to the throne of a kingdom of dragons and gods. ",
          ["Fantasy", "Adventure"], ["Dragons", "Gods", "Magic"], pop=6000, country="CN", year=2020),
]


@pytest.fixture(scope="session")
def frame():
    return build(RAW, [])


@pytest.fixture(scope="session")
def catalog(frame):
    emb = HashEmbedder()
    vectors = np.stack([emb.vec(doc) for doc in frame["doc"]])
    return Catalog(frame, vectors, emb, {"model": "hash", "built_at": "2026-10-23"})


@pytest.fixture(scope="session")
def keyword_catalog(frame):
    return Catalog(frame, None, None, {})
