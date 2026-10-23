"""
Pull manga, manhwa and manhua from the AniList GraphQL API.

Titles are fetched in popularity order and written as raw JSON lines, so the
dataset builder can be re-run without hitting the API again.

AniList asks clients to stay under its per-minute limit, so requests are
spaced out and a 429 waits for the Retry-After header before trying again.

Usage: python pipeline/fetch_anilist.py --max 15000 --out data/raw/anilist.jsonl.gz
"""
import argparse
import gzip
import json
import sys
import time

import requests

URL = "https://graphql.anilist.co"

QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(type: MANGA, sort: POPULARITY_DESC, isAdult: false) {
      id
      title { romaji english native }
      synonyms
      format
      status
      description(asHtml: false)
      startDate { year }
      chapters
      volumes
      meanScore
      popularity
      favourites
      genres
      tags { name rank isMediaSpoiler isAdult }
      countryOfOrigin
      coverImage { extraLarge large color }
      siteUrl
      staff(perPage: 4, sort: RELEVANCE) { edges { role node { name { full } } } }
    }
  }
}
"""


def fetch_page(session: requests.Session, page: int, per_page: int) -> dict:
    for attempt in range(8):
        resp = session.post(URL, json={"query": QUERY, "variables": {"page": page, "perPage": per_page}}, timeout=60)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "60")) + 1
            print(f"  rate limited, waiting {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        resp.raise_for_status()
        body = resp.json()
        if body.get("errors"):
            raise RuntimeError(body["errors"])
        return body["data"]["Page"]
    raise RuntimeError(f"page {page} failed after retries")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=15000)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--delay", type=float, default=2.2, help="seconds between requests")
    parser.add_argument("--out", default="data/raw/anilist.jsonl.gz")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    seen, written, page = set(), 0, 1
    with gzip.open(args.out, "wt", encoding="utf-8") as out:
        while written < args.max:
            data = fetch_page(session, page, args.per_page)
            for media in data["media"]:
                if media["id"] in seen:
                    continue
                seen.add(media["id"])
                out.write(json.dumps(media, ensure_ascii=False) + "\n")
                written += 1
            if page % 20 == 0:
                print(f"page {page}: {written} titles", flush=True)
            if not data["pageInfo"]["hasNextPage"] or not data["media"]:
                break
            page += 1
            time.sleep(args.delay)

    print(f"AniList: wrote {written} titles to {args.out}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
