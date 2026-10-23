"""
Pull Western comic series from Metron (metron.cloud).

Needs a free API token in METRON_API_TOKEN (or, the older way, the account's
METRON_USERNAME and METRON_PASSWORD). Without either the script prints a
notice and exits cleanly, so the pipeline still builds without Western titles.

Metron allows about 20 requests a minute and 5,000 a day on a free account,
so the walk is:
  1. page through the series list (cheap, about 100 series per request)
  2. keep the longest-running series and fetch their detail (synopsis, genres)
  3. fetch one cover per kept series from its issue list
Requests are spaced out and follow the X-RateLimit / Retry-After headers.

Output is plain JSON lines flushed after every series into <out>.partial, which
replaces <out> only when the walk finishes. A run cut off by a time limit
leaves the previous dump untouched; the workflow promotes the .partial file
only when there is no earlier dump to fall back on.

Usage: python pipeline/fetch_metron.py --max 1500 --out data/raw/metron.jsonl
"""
import argparse
import json
import os
import re
import sys
import time

import requests

BASE = "https://metron.cloud/api"
SKIP_TYPES = re.compile(r"trade|hardcover|omnibus|digital|graphic novel|annual|tpb", re.IGNORECASE)
SKIP_NAMES = re.compile(r"\b(tpb|omnibus|hc|collection|compendium|library edition)\b", re.IGNORECASE)
SKIP_PUBLISHERS = {"viz media", "kodansha comics", "yen press", "seven seas entertainment", "tokyopop"}


class Client:
    def __init__(self, token: str, gap: float, daily_budget: int, basic: tuple[str, str] | None = None):
        self.session = requests.Session()
        if basic:
            self.session.auth = basic
        else:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "imazinthecomicz-dataset-builder/2.0 (github.com/SlazzInC0de/imazinthecomicz)",
        })
        self.gap, self.budget, self.used, self.last = gap, daily_budget, 0, 0.0

    def get(self, url: str, params: dict | None = None) -> dict:
        for attempt in range(6):
            # checked on every attempt, so retries cannot run past the cap
            if self.used >= self.budget:
                raise RuntimeError("daily request budget used up")
            wait = self.gap - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.used += 1
            try:
                resp = self.session.get(url if url.startswith("http") else f"{BASE}/{url}", params=params,
                                        timeout=60)
            except requests.RequestException as exc:  # timeouts, resets
                print(f"  network error ({exc.__class__.__name__})", flush=True)
                if attempt < 5:  # no point waiting after the last attempt
                    time.sleep(10 * (attempt + 1))
                continue
            if resp.status_code == 429:
                pause = int(resp.headers.get("Retry-After", "65"))
                print(f"  rate limited, waiting {pause}s", flush=True)
                if attempt < 5:
                    time.sleep(pause + 1)
                continue
            if resp.status_code >= 500:
                if attempt < 5:
                    time.sleep(10 * (attempt + 1))
                continue
            if resp.status_code in (401, 403):
                print(f"::error::Metron refused the token ({resp.status_code}). Check the METRON_* secrets.")
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(f"{url} failed after retries")


def list_series(client: Client) -> list[dict]:
    out, url = [], "series/"
    while url:
        page = client.get(url)
        out.extend(page.get("results", []))
        url = page.get("next")
        if len(out) % 2000 < 100:
            print(f"series list: {len(out)}", flush=True)
    return out


def first_cover(client: Client, series_id: int) -> str | None:
    page = client.get(f"series/{series_id}/issue_list/")
    for issue in page.get("results", []):
        if issue.get("image"):
            return issue["image"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=1500, help="series to fetch in detail")
    parser.add_argument("--min-issues", type=int, default=6)
    parser.add_argument("--gap", type=float, default=3.2, help="seconds between requests")
    parser.add_argument("--budget", type=int, default=4800, help="requests allowed this run")
    parser.add_argument("--out", default="data/raw/metron.jsonl")
    args = parser.parse_args()

    token = os.environ.get("METRON_API_TOKEN", "").strip()
    user = os.environ.get("METRON_USERNAME", "").strip()
    password = os.environ.get("METRON_PASSWORD", "")
    if not token and not (user and password):
        print("No Metron credentials set, skipping Western comics.")
        return 0

    client = Client(token, args.gap, args.budget, basic=None if token else (user, password))
    try:
        listing = list_series(client)
    except Exception as exc:
        print(f"::warning::Metron series list failed: {exc}")
        return 0
    name = lambda s: s.get("series") or s.get("display_name") or s.get("name") or ""  # noqa: E731
    candidates = [s for s in listing
                  if (s.get("issue_count") or 0) >= args.min_issues and not SKIP_NAMES.search(name(s))]
    candidates.sort(key=lambda s: -(s.get("issue_count") or 0))
    print(f"Metron: {len(listing)} series listed, {len(candidates)} candidates", flush=True)

    written, complete = 0, True
    tmp = args.out + ".partial"
    with open(tmp, "w", encoding="utf-8") as out:
        for s in candidates:
            if written >= args.max:
                break
            try:
                detail = client.get(f"series/{s['id']}/")
                series_type = ((detail.get("series_type") or {}).get("name") or "")
                publisher = ((detail.get("publisher") or {}).get("name") or "").lower()
                if SKIP_TYPES.search(series_type) or publisher in SKIP_PUBLISHERS:
                    continue
                if len((detail.get("desc") or "").strip()) < 80:
                    continue
                detail["cover"] = first_cover(client, s["id"])
            except RuntimeError as exc:
                print(f"::warning::Metron fetch stopped at {written} series: {exc}")
                complete = False
                break
            except requests.HTTPError as exc:
                print(f"  skip series {s['id']}: {exc}")
                continue
            out.write(json.dumps(detail, ensure_ascii=False) + "\n")
            out.flush()
            written += 1
            if written % 100 == 0:
                print(f"kept {written} series ({client.used} requests)", flush=True)

    if complete or not os.path.exists(args.out):
        os.replace(tmp, args.out)
    else:
        os.remove(tmp)
        print(f"::warning::Metron refresh incomplete, keeping the previous {args.out}")
    print(f"Metron: fetched {written} series using {client.used} requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
