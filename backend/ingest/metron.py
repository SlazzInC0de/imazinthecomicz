"""Fetch Western comic series from the Metron API (https://metron.cloud).

Metron needs a free account. Set credentials in the environment:
    METRON_USERNAME=...  METRON_PASSWORD=...

How it works:
  1. Crawl the full series list once (cheap: 100 series per call). Each list
     item already carries publisher and issue_count. Saved to
     data/raw/metron_index.jsonl so later runs skip this step.
  2. Pick the biggest series per bucket (Marvel, DC, everyone else), ranked by
     issue_count, so flagship titles like Amazing Spider-Man, Batman and
     Detective Comics come first.
  3. Fetch details (+ optional issue #1 cover) for the picked series.
     Resumable: series already in metron.jsonl are skipped, so a dropped
     connection never loses progress. Just run the same command again.

Metron allows about 30 requests per minute, so calls are throttled.

Usage:
    python -m backend.ingest.metron --marvel 500 --dc 500 --others 500 --covers
"""
import argparse
import json
import os
import time
from pathlib import Path

import httpx

from ..normalize import western_kind

API_URL = "https://metron.cloud/api"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DELAY = 2.1  # seconds between calls, keeps us under 30 req/min


def _get(client: httpx.Client, url: str, params: dict | None = None) -> dict:
    for attempt in range(6):
        try:
            resp = client.get(url, params=params)
        except httpx.TransportError as exc:
            wait = 10 * (attempt + 1)
            print(f"Network error ({exc.__class__.__name__}), retrying in {wait}s")
            time.sleep(wait)
            continue
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        time.sleep(DELAY)
        return resp.json()
    raise RuntimeError(f"Metron request failed: {url}")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def crawl_series_index(client: httpx.Client, path: Path, refresh: bool) -> list[dict]:
    """Every series on Metron with publisher + issue_count, cached on disk."""
    if path.exists() and not refresh:
        items = _read_jsonl(path)
        print(f"Using cached series index ({len(items)} series). Pass --refresh-index to re-crawl.")
        return items
    items: list[dict] = []
    url: str | None = f"{API_URL}/series/"
    while url:
        page = _get(client, url)
        items.extend(page.get("results", []))
        print(f"Series index: {len(items)} / {page.get('count', '?')}")
        url = page.get("next")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return items


def pick_series(index: list[dict], marvel: int, dc: int, others: int, min_issues: int) -> list[dict]:
    """Biggest series first within each bucket, interleaved so every bucket fills early."""
    buckets: dict[str, list[dict]] = {"Marvel": [], "DC": [], "Western": []}
    for item in index:
        if (item.get("issue_count") or 0) < min_issues:
            continue
        publisher = (item.get("publisher") or {}).get("name")
        buckets[western_kind(publisher)].append(item)
    limits = {"Marvel": marvel, "DC": dc, "Western": others}
    for kind, items in buckets.items():
        items.sort(key=lambda s: s.get("issue_count") or 0, reverse=True)
        buckets[kind] = items[: limits[kind]]
        print(f"Picked {len(buckets[kind])} {kind} series")
    picked: list[dict] = []
    for i in range(max(limits.values())):
        for kind in ("Marvel", "DC", "Western"):
            if i < len(buckets[kind]):
                picked.append(buckets[kind][i])
    return picked


def first_issue_cover(client: httpx.Client, series_id: int) -> str | None:
    data = _get(client, f"{API_URL}/issue/", {"series_id": series_id, "number": 1})
    for issue in data.get("results", []):
        if issue.get("image"):
            return issue["image"]
        return _get(client, f"{API_URL}/issue/{issue['id']}/").get("image")
    return None


def run(args: argparse.Namespace) -> int:
    user = os.environ.get("METRON_USERNAME")
    password = os.environ.get("METRON_PASSWORD")
    if not user or not password:
        raise SystemExit("Set METRON_USERNAME and METRON_PASSWORD first.")

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_jsonl(out)
    done = {s["id"] for s in existing}
    with httpx.Client(timeout=30, auth=(user, password)) as client:
        index = crawl_series_index(client, out.parent / "metron_index.jsonl", args.refresh_index)
        picked = [s for s in pick_series(index, args.marvel, args.dc, args.others, args.min_issues) if s["id"] not in done]
        calls = len(picked) * (2 if args.covers else 1)
        print(f"{len(done)} series already saved, {len(picked)} to fetch (~{calls * DELAY / 60:.0f} min)")
        with out.open("a", encoding="utf-8") as fh:
            for n, item in enumerate(picked, 1):
                detail = _get(client, f"{API_URL}/series/{item['id']}/")
                if args.covers:
                    detail["cover"] = first_issue_cover(client, item["id"])
                fh.write(json.dumps(detail, ensure_ascii=False) + "\n")
                fh.flush()
                if n % 25 == 0:
                    print(f"Metron: {n}/{len(picked)} fetched (latest: {detail.get('name')})")
    return len(done) + len(picked)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Western comics from Metron")
    parser.add_argument("--marvel", type=int, default=500, help="Top Marvel series by issue count")
    parser.add_argument("--dc", type=int, default=500, help="Top DC series by issue count")
    parser.add_argument("--others", type=int, default=500, help="Top series from all other Western publishers")
    parser.add_argument("--min-issues", type=int, default=3, help="Skip series shorter than this")
    parser.add_argument("--covers", action="store_true", help="Also fetch issue #1 cover (1 extra call per series)")
    parser.add_argument("--refresh-index", action="store_true", help="Re-crawl the full series list")
    parser.add_argument("--out", type=Path, default=RAW_DIR / "metron.jsonl")
    args = parser.parse_args()
    total = run(args)
    print(f"Done. {total} series in {args.out}")
