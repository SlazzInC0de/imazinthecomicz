"""Fetch Western comic series from the Metron API (https://metron.cloud).

Metron needs a free account. Set credentials in the environment:
    METRON_USERNAME=...  METRON_PASSWORD=...

Metron allows about 30 requests per minute, so detail calls are throttled.

Usage:
    python -m backend.ingest.metron --limit 300
"""
import argparse
import json
import os
import time
from pathlib import Path

import httpx

API_URL = "https://metron.cloud/api"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DELAY = 2.1  # seconds between calls, keeps us under 30 req/min


def _get(client: httpx.Client, url: str, params: dict | None = None) -> dict:
    for _ in range(5):
        resp = client.get(url, params=params)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        time.sleep(DELAY)
        return resp.json()
    raise RuntimeError(f"Metron request failed: {url}")


def first_issue_cover(client: httpx.Client, series_id: int) -> str | None:
    data = _get(client, f"{API_URL}/issue/", {"series_id": series_id, "number": 1})
    for issue in data.get("results", []):
        detail = _get(client, f"{API_URL}/issue/{issue['id']}/")
        return detail.get("image")
    return None


def run(limit: int, out: Path, covers: bool) -> int:
    user = os.environ.get("METRON_USERNAME")
    password = os.environ.get("METRON_PASSWORD")
    if not user or not password:
        raise SystemExit("Set METRON_USERNAME and METRON_PASSWORD first.")

    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    url: str | None = f"{API_URL}/series/"
    with httpx.Client(timeout=30, auth=(user, password)) as client, out.open("w", encoding="utf-8") as fh:
        while url and count < limit:
            page = _get(client, url)
            for item in page.get("results", []):
                if count >= limit:
                    break
                detail = _get(client, f"{API_URL}/series/{item['id']}/")
                if covers:
                    detail["cover"] = first_issue_cover(client, item["id"])
                fh.write(json.dumps(detail, ensure_ascii=False) + "\n")
                count += 1
                if count % 25 == 0:
                    print(f"Metron: {count} series")
            url = page.get("next")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Western comics from Metron")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--covers", action="store_true", help="Also fetch issue #1 cover (3 extra calls per series)")
    parser.add_argument("--out", type=Path, default=RAW_DIR / "metron.jsonl")
    args = parser.parse_args()
    total = run(args.limit, args.out, args.covers)
    print(f"Saved {total} series to {args.out}")
