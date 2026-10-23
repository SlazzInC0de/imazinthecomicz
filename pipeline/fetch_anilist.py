"""
Pull manga, manhwa and manhua from the AniList GraphQL API.

Titles are fetched in popularity order and written as raw JSON lines, so the
dataset builder can be re-run without hitting the API again.

AniList stops paginating after 5,000 results per query, so the walk is split
into windows: when a window runs out, the next one asks for titles less
popular than the last one seen and carries on from there.

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
query ($page: Int, $perPage: Int__BELOW_VAR__) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(type: MANGA, sort: POPULARITY_DESC, isAdult: false__BELOW_ARG__) {
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


WINDOW = 5000


def fetch_page(session: requests.Session, page: int, per_page: int, below: int | None) -> dict:
    # AniList rejects popularity_lesser: null, so the filter is only added when set
    variables = {"page": page, "perPage": per_page}
    query = QUERY.replace("__BELOW_VAR__", "").replace("__BELOW_ARG__", "")
    if below is not None:
        variables["below"] = below
        query = QUERY.replace("__BELOW_VAR__", ", $below: Int").replace("__BELOW_ARG__", ", popularity_lesser: $below")
    for attempt in range(8):
        resp = session.post(URL, json={"query": query, "variables": variables}, timeout=60)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "60")) + 1
            print(f"  rate limited, waiting {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        if resp.status_code >= 400:
            # GitHub turns ::error:: lines into annotations, readable without the log
            print(f"::error::AniList {resp.status_code} on page {page} (below={below}): {resp.text[:300]}", flush=True)
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

    seen, written, page, below, lowest = set(), 0, 1, None, None
    pages_per_window = WINDOW // args.per_page
    with gzip.open(args.out, "wt", encoding="utf-8") as out:
        while written < args.max:
            try:
                data = fetch_page(session, page, args.per_page, below)
            except Exception as exc:  # keep what we have instead of losing the whole run
                print(f"::warning::AniList fetch stopped early at {written} titles: {exc}", flush=True)
                break
            new = 0
            for media in data["media"]:
                lowest = media.get("popularity") if lowest is None else min(lowest, media.get("popularity") or 0)
                if media["id"] in seen:
                    continue
                seen.add(media["id"])
                out.write(json.dumps(media, ensure_ascii=False) + "\n")
                written += 1
                new += 1
            if page % 20 == 0:
                print(f"window below={below} page {page}: {written} titles", flush=True)
            if not data["media"]:
                break
            if new == 0 and page == 1 and below is not None:
                # a whole page of ties we already have: step strictly below them
                below, lowest = below - 1, below - 1
                if below <= 0:
                    break
                time.sleep(args.delay)
                continue
            if page >= pages_per_window or not data["pageInfo"]["hasNextPage"]:
                if not data["pageInfo"]["hasNextPage"] and page < pages_per_window:
                    break  # reached the true end of the list
                # +1 keeps titles that tie with the last one; duplicates are skipped by id
                below, page = (lowest or 0) + 1, 1
            else:
                page += 1
            time.sleep(args.delay)

    print(f"AniList: wrote {written} titles to {args.out}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
