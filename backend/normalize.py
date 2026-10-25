"""Map raw AniList and Metron records onto one catalog schema."""
import re
from typing import Any

TAG_MIN_RANK = 60  # keep only tags AniList voters rate as strongly relevant

FORMAT_LABELS = {"MANGA": "Manga", "ONE_SHOT": "One-shot", "NOVEL": "Light novel"}
COUNTRY_FORMAT = {"KR": "Manhwa", "CN": "Manhua", "TW": "Manhua"}


# A Wikipedia match is only kept when its page is about the comic, not a film,
# show, game or company that shares the name. The subject (whose name may
# contain "song" or "film") is skipped, and so is anything after "based on".
_COMIC_WORDS = re.compile(r"comic|manga|manhwa|manhua|graphic novel|webtoon|webcomic|superhero(?:es|ine)?(?! film)|supervillain|\bcharacters?\b")
_OTHER_WORDS = re.compile(r"\bfilms?\b|television|\btv\b|anime series|animation series|video game|\bgame\b|\bstudios?\b|\balbums?\b|\bsongs?\b|\bnovels?\b|\bband\b|\bmusical\b|\bfranchise\b|\bcompany\b")
_OTHER_TITLE = re.compile(r"\((?:[^)]*\b)?(film|films|film series|tv series|television series|video game|novel|album|song|miniseries|franchise)\)", re.I)


def is_comic_page(title: str, extract: str) -> bool:
    if _OTHER_TITLE.search(title or ""):
        return False
    head = (extract or "")[:400].lower()
    verb = re.search(r"\b(is|are|was|were)\b", head)
    head = head[verb.end():] if verb else head
    head = re.split(r" based on | adapted from | adaptation of | inspired by ", head, maxsplit=1)[0]
    comic, other = _COMIC_WORDS.search(head), _OTHER_WORDS.search(head)
    return bool(comic) and (not other or comic.start() < other.start())


def clean_text(text: Any) -> str:
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", " ", str(text))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\(Source:[^)]*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def from_anilist(m: dict) -> dict:
    title = m["title"].get("english") or m["title"].get("romaji") or "Untitled"
    country = m.get("countryOfOrigin") or "JP"
    tags = [t["name"] for t in m.get("tags") or [] if t.get("rank", 0) >= TAG_MIN_RANK and not t.get("isMediaSpoiler")]
    creators = [
        f'{e["node"]["name"]["full"]} ({e["role"]})'
        for e in (m.get("staff") or {}).get("edges", [])
        if e.get("node")
    ]
    score = m.get("averageScore")
    return {
        "id": f"al-{m['id']}",
        "source": "anilist",
        "kind": COUNTRY_FORMAT.get(country, FORMAT_LABELS.get(m.get("format"), "Manga")),
        "title": title,
        "alt_title": m["title"].get("romaji") if m["title"].get("romaji") != title else None,
        "description": clean_text(m.get("description")),
        "genres": m.get("genres") or [],
        "tags": tags[:12],
        "publisher": None,
        "creators": creators,
        "year": (m.get("startDate") or {}).get("year"),
        "status": (m.get("status") or "").replace("_", " ").title() or None,
        "country": country,
        "score": round(score / 10, 1) if score else None,
        "popularity": m.get("popularity") or 0,
        "volumes": m.get("volumes"),
        "chapters": m.get("chapters"),
        "cover": (m.get("coverImage") or {}).get("large"),
        "color": (m.get("coverImage") or {}).get("color"),
        "url": m.get("siteUrl"),
    }


def western_kind(publisher: str | None) -> str:
    """Marvel and DC get their own bucket, every other Western publisher stays 'Western'."""
    name = (publisher or "").strip().lower()
    if name.startswith("marvel"):
        return "Marvel"
    if name == "dc" or name.startswith("dc "):
        return "DC"
    return "Western"


def from_metron(s: dict) -> dict:
    publisher = (s.get("publisher") or {}).get("name")
    year_began, year_end = s.get("year_began"), s.get("year_end")
    return {
        "id": f"mt-{s['id']}",
        "source": "metron",
        "kind": western_kind(publisher),
        "title": s.get("name") or "Untitled",
        "alt_title": f"Vol. {s['volume']} ({year_began})" if s.get("volume") and year_began else None,
        "description": clean_text(s.get("desc")),
        "genres": [g["name"] for g in s.get("genres") or []],
        "tags": [(s.get("series_type") or {}).get("name")] if s.get("series_type") else [],
        "publisher": publisher,
        "creators": [],
        "year": year_began,
        "status": "Finished" if year_end else "Ongoing",
        "country": "US",
        "score": None,
        "popularity": s.get("issue_count") or 0,
        "volumes": s.get("volume"),
        "chapters": s.get("issue_count"),
        "cover": s.get("cover"),
        "color": None,
        "url": f"https://metron.cloud/series/{s['id']}/",
    }


def semantic_doc(c: dict) -> str:
    """Text the embedding model sees. Description carries most of the meaning."""
    parts = [f"{c['title']} ({c['kind']})."]
    if c["genres"]:
        parts.append("Genres: " + ", ".join(c["genres"]) + ".")
    if c["tags"]:
        parts.append("Themes: " + ", ".join(t for t in c["tags"] if t) + ".")
    if c["publisher"]:
        parts.append(f"Publisher: {c['publisher']}.")
    if c["description"]:
        parts.append(c["description"][:1200])
    extract = c.get("wiki_extract")
    if extract and extract != c["description"]:
        parts.append(extract[:600])
    return " ".join(parts)
