"""
Pull Western comic series (Comic Vine "volumes") with their descriptions.

Needs a free API key in the COMICVINE_API_KEY environment variable. Without
one the script prints a notice and exits cleanly, so the pipeline still builds
a manga-only catalog.

Comic Vine allows about 200 requests per hour per resource and dislikes
bursts, so requests are spaced out and an hourly budget is enforced.

Usage: python pipeline/fetch_comicvine.py --max 6000 --out data/raw/comicvine.jsonl.gz
"""
import argparse
import gzip
import json
import os
import sys
import time

import requests

BASE = "https://comicvine.gamespot.com/api"
FIELDS = "id,name,deck,description,start_year,publisher,count_of_issues,image,site_detail_url"

# Imprints that mostly reprint manga or translate US books; AniList already
# covers the manga and the translations would duplicate the originals.
SKIP_PUBLISHERS = {
    "viz", "viz media", "kodansha comics", "kodansha", "yen press", "seven seas entertainment",
    "tokyopop", "shueisha", "square enix", "vertical", "del rey", "j-novel club", "denpa",
    "panini comics", "panini verlag", "panini france", "panini españa", "editorial televisa",
    "planeta deagostini", "ecc ediciones", "urban comics", "ediciones zinco", "rw edizioni",
    "editora abril", "egmont", "semic", "carlsen", "glénat manga", "kana", "pika édition",
}


class Budget:
    """Keeps requests under the hourly cap and at least `gap` seconds apart."""

    def __init__(self, per_hour: int, gap: float):
        self.per_hour, self.gap, self.stamps, self.last = per_hour, gap, [], 0.0

    def wait(self):
        now = time.time()
        self.stamps = [t for t in self.stamps if now - t < 3600]
        if len(self.stamps) >= self.per_hour:
            pause = 3600 - (now - self.stamps[0]) + 5
            print(f"  hourly budget used, sleeping {pause:.0f}s", flush=True)
            time.sleep(pause)
        delta = time.time() - self.last
        if delta < self.gap:
            time.sleep(self.gap - delta)
        self.last = time.time()
        self.stamps.append(self.last)


def get(session, budget, path, params):
    for attempt in range(6):
        budget.wait()
        resp = session.get(f"{BASE}/{path}/", params=params, timeout=60)
        if resp.status_code in (420, 429):
            time.sleep(60 * (attempt + 1))
            continue
        if resp.status_code >= 500:
            time.sleep(10 * (attempt + 1))
            continue
        resp.raise_for_status()
        body = resp.json()
        if body.get("status_code") != 1:
            raise RuntimeError(body.get("error"))
        return body
    raise RuntimeError(f"{path} failed after retries")


def keep(vol: dict, min_issues: int) -> bool:
    publisher = ((vol.get("publisher") or {}).get("name") or "").strip().lower()
    if not publisher or publisher in SKIP_PUBLISHERS:
        return False
    if (vol.get("count_of_issues") or 0) < min_issues:
        return False
    text = (vol.get("deck") or "") + (vol.get("description") or "")
    return len(text) >= 150


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=6000)
    parser.add_argument("--max-requests", type=int, default=400)
    parser.add_argument("--min-issues", type=int, default=4)
    parser.add_argument("--out", default="data/raw/comicvine.jsonl.gz")
    args = parser.parse_args()

    key = os.environ.get("COMICVINE_API_KEY", "").strip()
    if not key:
        print("COMICVINE_API_KEY not set, skipping Western comics.")
        return 0

    session = requests.Session()
    # Comic Vine rejects the default python-requests user agent.
    session.headers["User-Agent"] = "imazinthecomicz-dataset-builder/2.0 (github.com/SlazzInC0de/imazinthecomicz)"
    budget = Budget(per_hour=190, gap=1.2)
    base = {"api_key": key, "format": "json", "field_list": FIELDS, "limit": 100}

    # Long-running series first: they are the ones people actually search for.
    first = get(session, budget, "volumes", {**base, "sort": "count_of_issues:desc", "offset": 0})
    counts = [v.get("count_of_issues") or 0 for v in first["results"]]
    if counts != sorted(counts, reverse=True):
        print("Comic Vine ignored the sort parameter, results will be in id order.")

    seen, written, requests_made, offset = set(), 0, 1, 0
    page = first
    with gzip.open(args.out, "wt", encoding="utf-8") as out:
        while True:
            for vol in page["results"]:
                if vol["id"] in seen or not keep(vol, args.min_issues):
                    continue
                seen.add(vol["id"])
                out.write(json.dumps(vol, ensure_ascii=False) + "\n")
                written += 1
            offset += 100
            if written >= args.max or requests_made >= args.max_requests or offset >= page["number_of_total_results"]:
                break
            page = get(session, budget, "volumes", {**base, "sort": "count_of_issues:desc", "offset": offset})
            requests_made += 1
            if requests_made % 10 == 0:
                print(f"request {requests_made}: {written} series kept", flush=True)

    print(f"Comic Vine: wrote {written} series to {args.out} using {requests_made} requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
