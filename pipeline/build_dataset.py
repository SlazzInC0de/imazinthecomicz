"""
Merge the raw AniList, Comic Vine and Metron dumps into one clean catalog.

Every row ends up with the same fields whatever its source, plus the text that
gets embedded (`doc`) and the tone / scope percentiles behind the vibe sliders.

Usage: python pipeline/build_dataset.py --out data/catalog.parquet
"""
import argparse
import gzip
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from text import clean_description, first_paragraphs  # noqa: E402
from vibe import raw_scores, to_percentiles, western_genres  # noqa: E402

KIND_BY_COUNTRY = {"JP": "Manga", "KR": "Manhwa", "CN": "Manhua", "TW": "Manhua"}
STATUS = {"FINISHED": "Completed", "RELEASING": "Ongoing", "HIATUS": "Hiatus", "CANCELLED": "Cancelled"}
FORMAT = {"MANGA": "Series", "ONE_SHOT": "One-shot"}
MIN_DESCRIPTION = 80
TAG_MIN_RANK = 50


def read_jsonl(path: str):
    if not os.path.exists(path):
        return []
    opener = gzip.open if path.endswith(".gz") else open
    rows = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # a run cut off mid-write can leave half a line at the end
    return rows


def creators_from_staff(media: dict) -> list[str]:
    names = []
    for edge in (media.get("staff") or {}).get("edges", []):
        role = (edge.get("role") or "").lower()
        name = edge["node"]["name"]["full"]
        if any(word in role for word in ("story", "art", "original creator")) and name not in names:
            names.append(name)
    return names[:3]


def anilist_row(media: dict) -> dict | None:
    if media.get("format") not in FORMAT or media.get("status") not in STATUS:
        return None
    description = clean_description(media.get("description"))
    if len(description) < MIN_DESCRIPTION:
        return None
    title = media["title"].get("english") or media["title"].get("romaji")
    alt = [t for t in (media["title"].get("romaji"), media["title"].get("native"), *(media.get("synonyms") or []))
           if t and t != title]
    tags = [t for t in media.get("tags") or [] if not t.get("isAdult")]
    shown_tags = [t["name"] for t in sorted(tags, key=lambda t: -(t.get("rank") or 0))
                  if not t.get("isMediaSpoiler") and (t.get("rank") or 0) >= TAG_MIN_RANK][:8]
    tone, scope = raw_scores(media.get("genres") or [], [t for t in tags if not t.get("isMediaSpoiler")])
    cover = media.get("coverImage") or {}
    return {
        "id": f"al-{media['id']}",
        "source": "AniList",
        "title": title,
        "alt_titles": alt[:5],
        "kind": KIND_BY_COUNTRY.get(media.get("countryOfOrigin"), "Western"),
        "format": FORMAT[media["format"]],
        "year": (media.get("startDate") or {}).get("year"),
        "status": STATUS[media["status"]],
        "length": media.get("chapters") or None,
        "length_unit": "chapters",
        "score": media.get("meanScore"),
        "popularity": media.get("popularity") or 0,
        "genres": media.get("genres") or [],
        "tags": shown_tags,
        "creators": creators_from_staff(media),
        "publisher": None,
        "description": first_paragraphs(description),
        "cover": cover.get("extraLarge") or cover.get("large"),
        "cover_color": cover.get("color"),
        "url": media.get("siteUrl"),
        "tone_raw": tone,
        "scope_raw": scope,
    }


def comicvine_row(vol: dict) -> dict | None:
    deck = clean_description(vol.get("deck"))
    body = clean_description(vol.get("description"))
    description = deck if len(body) < len(deck) else (f"{deck}\n\n{body}" if deck and deck not in body else body)
    if len(description) < MIN_DESCRIPTION:
        return None
    description = first_paragraphs(description)
    genres = western_genres(f"{vol.get('name', '')} {description}")
    tone, scope = raw_scores(genres, [])
    year = vol.get("start_year")
    try:
        year = int(year) if year else None
    except ValueError:
        year = None
    image = vol.get("image") or {}
    return {
        "id": f"cv-{vol['id']}",
        "source": "Comic Vine",
        "title": vol["name"].strip(),
        "alt_titles": [],
        "kind": "Western",
        "format": "Series",
        "year": year,
        "status": None,
        "length": vol.get("count_of_issues") or None,
        "length_unit": "issues",
        "score": None,
        "popularity": (vol.get("count_of_issues") or 0) * 40,
        "genres": genres,
        "tags": [],
        "creators": [],
        "publisher": (vol.get("publisher") or {}).get("name"),
        "description": description,
        "cover": image.get("super_url") or image.get("medium_url"),
        "cover_color": None,
        "url": vol.get("site_detail_url"),
        "tone_raw": tone,
        "scope_raw": scope,
    }


METRON_GENRES = {
    "Super-Hero": "Superhero", "Superhero": "Superhero", "Science Fiction": "Sci-Fi", "Humor": "Comedy",
    "Horror": "Horror", "Crime": "Crime", "Fantasy": "Fantasy", "Romance": "Romance", "War": "War",
    "Western": "Western", "Adventure": "Adventure", "Mystery": "Mystery", "Drama": "Drama", "Sports": "Sports",
    "Espionage": "Thriller", "Teen": "Slice of Life", "Historical": "Drama",
}


def metron_row(series: dict) -> dict | None:
    description = clean_description(series.get("desc"))
    if len(description) < MIN_DESCRIPTION:
        return None
    description = first_paragraphs(description)
    title = (series.get("name") or series.get("series") or "").strip()
    if not title:
        return None
    genres = []
    for g in series.get("genres") or []:
        mapped = METRON_GENRES.get(g.get("name") if isinstance(g, dict) else str(g))
        if mapped and mapped not in genres:
            genres.append(mapped)
    for g in western_genres(f"{title} {description}"):
        if g not in genres and len(genres) < 4:
            genres.append(g)
    tone, scope = raw_scores(genres, [])
    series_type = ((series.get("series_type") or {}).get("name") or "")
    status = "Completed" if series.get("year_end") else ("Cancelled" if "cancel" in series_type.lower() else "Ongoing")
    issues = series.get("issue_count") or 0
    return {
        "id": f"mt-{series['id']}",
        "source": "Metron",
        "title": title,
        "alt_titles": [],
        "kind": "Western",
        "format": "One-shot" if "one-shot" in series_type.lower() else "Series",
        "year": series.get("year_began"),
        "status": status,
        "length": issues or None,
        "length_unit": "issues",
        "score": None,
        "popularity": issues * 40,
        "genres": genres,
        "tags": [],
        "creators": [],
        "publisher": (series.get("publisher") or {}).get("name"),
        "description": description,
        "cover": series.get("cover"),
        "cover_color": None,
        "url": series.get("resource_url"),
        "tone_raw": tone,
        "scope_raw": scope,
    }


def embedding_doc(row: dict) -> str:
    parts = [row["title"]]
    if row["alt_titles"]:
        parts.append("Also known as " + ", ".join(row["alt_titles"][:3]))
    parts.append(f"{row['kind']} {row['format'].lower()}" + (f" from {row['year']}" if row["year"] else ""))
    if row["genres"]:
        parts.append("Genres: " + ", ".join(row["genres"]))
    if row["tags"]:
        parts.append("Themes: " + ", ".join(row["tags"]))
    if row["creators"]:
        parts.append("By " + ", ".join(row["creators"]))
    if row["publisher"]:
        parts.append("Published by " + row["publisher"])
    return ". ".join(parts) + ".\n" + row["description"]


def build(anilist: list, comicvine: list, metron: list | None = None) -> pd.DataFrame:
    rows = ([r for r in map(anilist_row, anilist) if r] + [r for r in map(comicvine_row, comicvine) if r]
            + [r for r in map(metron_row, metron or []) if r])
    if not rows:
        raise SystemExit("No rows to build from. Run the fetchers first.")
    for row in rows:
        row["doc"] = embedding_doc(row)
    df = pd.DataFrame(rows).drop_duplicates("id")
    # Same title and year from two sources: keep one (AniList, then Comic Vine, then Metron).
    df["_key"] = df["title"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + df["year"].astype(str)
    order = {"AniList": 0, "Comic Vine": 1, "Metron": 2}
    df = df.sort_values("source", key=lambda col: col.map(order)).drop_duplicates("_key").drop(columns="_key")
    df = df.sort_values("popularity", ascending=False).reset_index(drop=True)
    df["tone"] = to_percentiles(df["tone_raw"]).round(4)
    df["scope"] = to_percentiles(df["scope_raw"]).round(4)
    df = df.drop(columns=["tone_raw", "scope_raw"])
    df["year"] = df["year"].astype("Int64")
    df["length"] = df["length"].astype("Int64")
    df["score"] = df["score"].astype("Int64")
    return df


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anilist", default="data/raw/anilist.jsonl.gz")
    parser.add_argument("--comicvine", default="data/raw/comicvine.jsonl.gz")
    parser.add_argument("--metron", default="data/raw/metron.jsonl")
    parser.add_argument("--out", default="data/catalog.parquet")
    args = parser.parse_args()

    df = build(read_jsonl(args.anilist), read_jsonl(args.comicvine), read_jsonl(args.metron))
    df.to_parquet(args.out, index=False)
    print(f"Catalog: {len(df)} titles -> {args.out}")
    print(df["kind"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
