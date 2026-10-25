"""Enrich catalog entries with a Wikipedia intro paragraph.

Many Metron series (and some AniList titles) have little or no description,
which leaves the embedding model with almost nothing to understand. This step
looks each title up on Wikipedia once and caches the intro text in
data/raw/wiki.jsonl. Resumable: cached titles are skipped on re-runs.

Usage:
    python -m backend.ingest.wiki            # titles with short descriptions
    python -m backend.ingest.wiki --all      # every title
"""
import argparse
import json
import time
from pathlib import Path

import httpx

from ..aliases import normalize
from ..build_index import build_catalog
from ..normalize import is_comic_page

API_URL = "https://en.wikipedia.org/w/api.php"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
HEADERS = {"User-Agent": "imazinthecomics/2.0 (https://github.com/SlazzInC0de/imazinthecomicz)"}
SHORT_DESC = 200


def search_term(c: dict) -> str:
    if c["kind"] in ("Marvel", "DC", "Western"):
        return f"{c['title']} {c['publisher'] or ''} comic book".strip()
    return f"{c['title']} {c['kind'].lower()}"


def looks_right(c: dict, page_title: str) -> bool:
    """Reject results that share no word with the comic's title."""
    words = {w for w in normalize(c["title"]).split() if len(w) > 2} or set(normalize(c["title"]).split())
    page = normalize(page_title)
    return any(w in page for w in words)


def lookup(client: httpx.Client, c: dict) -> dict | None:
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": search_term(c),
        "gsrlimit": 1, "prop": "extracts|info", "exintro": 1, "explaintext": 1, "exchars": 900, "inprop": "url",
    }
    for attempt in range(4):
        try:
            resp = client.get(API_URL, params=params)
            resp.raise_for_status()
            break
        except httpx.HTTPError:
            time.sleep(5 * (attempt + 1))
    else:
        return None
    pages = (resp.json().get("query") or {}).get("pages") or {}
    for page in pages.values():
        if page.get("extract") and looks_right(c, page.get("title", "")) and is_comic_page(page.get("title", ""), page["extract"]):
            return {"wiki_title": page["title"], "wiki_extract": page["extract"].strip(), "wiki_url": page.get("fullurl")}
    return None


def run(all_titles: bool, out: Path) -> int:
    catalog = build_catalog()
    cached = set()
    if out.exists():
        with out.open(encoding="utf-8") as fh:
            cached = {json.loads(line)["id"] for line in fh if line.strip()}
    todo = [c for c in catalog if c["id"] not in cached and (all_titles or len(c["description"]) < SHORT_DESC)]
    print(f"{len(cached)} cached, {len(todo)} to look up")
    hits = 0
    with httpx.Client(timeout=20, headers=HEADERS) as client, out.open("a", encoding="utf-8") as fh:
        for n, c in enumerate(todo, 1):
            found = lookup(client, c)
            hits += bool(found)
            fh.write(json.dumps({"id": c["id"], **(found or {})}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(f"Wikipedia: {n}/{len(todo)} looked up, {hits} matched")
            time.sleep(0.1)
    return hits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add Wikipedia intros to catalog entries")
    parser.add_argument("--all", action="store_true", help="Look up every title, not just ones with short descriptions")
    parser.add_argument("--out", type=Path, default=RAW_DIR / "wiki.jsonl")
    args = parser.parse_args()
    print(f"Done. {run(args.all, args.out)} new matches saved to {args.out}")
