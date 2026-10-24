"""Fetch manga / manhwa / manhua from the public AniList GraphQL API.

No API key is needed. AniList allows roughly 90 requests per minute, so the
fetcher sleeps between pages and backs off on HTTP 429.

Usage:
    python -m backend.ingest.anilist --pages 40
"""
import argparse
import json
import time
from pathlib import Path

import httpx

API_URL = "https://graphql.anilist.co"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(type: MANGA, sort: POPULARITY_DESC, isAdult: false) {
      id
      siteUrl
      title { english romaji }
      description(asHtml: false)
      format
      status
      countryOfOrigin
      chapters
      volumes
      averageScore
      popularity
      startDate { year }
      genres
      tags { name rank isMediaSpoiler }
      coverImage { large color }
      staff(perPage: 4) { edges { role node { name { full } } } }
    }
  }
}
"""


def fetch_page(client: httpx.Client, page: int, per_page: int = 50) -> dict:
    for attempt in range(5):
        resp = client.post(API_URL, json={"query": QUERY, "variables": {"page": page, "perPage": per_page}})
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["data"]["Page"]
    raise RuntimeError(f"AniList page {page} failed after retries")


def run(pages: int, out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with httpx.Client(timeout=30) as client, out.open("w", encoding="utf-8") as fh:
        for page in range(1, pages + 1):
            data = fetch_page(client, page)
            for media in data["media"]:
                fh.write(json.dumps(media, ensure_ascii=False) + "\n")
                count += 1
            print(f"AniList page {page}: {count} titles so far")
            if not data["pageInfo"]["hasNextPage"]:
                break
            time.sleep(0.8)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch manga data from AniList")
    parser.add_argument("--pages", type=int, default=40, help="Pages of 50 titles each")
    parser.add_argument("--out", type=Path, default=RAW_DIR / "anilist.jsonl")
    args = parser.parse_args()
    total = run(args.pages, args.out)
    print(f"Saved {total} titles to {args.out}")
