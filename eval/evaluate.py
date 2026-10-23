"""
Retrieval benchmark for the search engine.

Relevance comes from AniList metadata: a title counts as relevant to a
descriptive query when it carries one of the query's genres or tags (tags only
count at rank 50% or more). Descriptive queries avoid the label words on
purpose, so keyword search cannot just look them up. Title queries check that
a known series shows up first when typed by name.

Rankers compared on the same catalog:
  random    expected precision = share of relevant titles
  keyword   BM25 only
  semantic  embedding cosine only
  hybrid    what the API serves (blend + title bonus + popularity)

Also prints the cosine of relevant vs irrelevant top-10 hits, to check whether a
fixed similarity cut-off could label results (so far it cannot, see results.md).

Usage: python eval/evaluate.py [--out eval/results.md]
"""
import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))

from app.embedder import FastEmbedder  # noqa: E402
from app.engine import Catalog, Filters, tokenize  # noqa: E402
from pathlib import Path  # noqa: E402


def relevant_mask(catalog: Catalog, rule: dict) -> np.ndarray:
    out = np.zeros(len(catalog.records), dtype=bool)
    genres, tags = set(rule.get("genres_any", [])), set(rule.get("tags_any", []))
    titles = [t.lower() for t in rule.get("title_contains", [])]
    for i, rec in enumerate(catalog.records):
        if genres & set(rec["genres"] or []) or tags & set(rec["tags"] or []):
            out[i] = True
        elif titles:
            names = [rec["title"].lower(), *[a.lower() for a in rec["alt_titles"] or []]]
            out[i] = any(t in n for t in titles for n in names)
    return out


def metrics(order: np.ndarray, relevant: np.ndarray) -> dict:
    hits = relevant[order[:10]]
    first = np.flatnonzero(relevant[order[:100]])
    return {"p5": hits[:5].mean(), "p10": hits.mean(), "mrr": 1 / (first[0] + 1) if len(first) else 0.0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=os.path.join(ROOT, "data"))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    catalog = Catalog.load(Path(args.data), FastEmbedder)
    if catalog.mode != "hybrid":
        print("Embeddings or model missing, cannot run the benchmark.")
        return 1
    queries = json.load(open(os.path.join(ROOT, "eval", "queries.json"), encoding="utf-8"))

    rows, totals = [], {}
    rel_cos, irr_cos = [], []
    for item in queries:
        relevant = relevant_mask(catalog, item)
        if not relevant.any():
            print(f"skip (no relevant titles in catalog): {item['query']}")
            continue
        qvec = catalog.embedder.embed_query(item["query"])
        semantic = catalog.vectors @ qvec
        keyword = catalog.bm25.score(tokenize(item["query"]))
        hybrid_hits, _ = catalog.search(item["query"], Filters(), limit=48)
        top = [h.index for h in hybrid_hits]
        seen = set(top)
        orders = {
            "keyword": np.argsort(-keyword, kind="stable"),
            "semantic": np.argsort(-semantic, kind="stable"),
            "hybrid": np.array(top + [i for i in np.argsort(-semantic) if i not in seen]),
        }
        scores = {name: metrics(order, relevant) for name, order in orders.items()}
        scores["random"] = {"p5": relevant.mean(), "p10": relevant.mean(), "mrr": float("nan")}
        for name, s in scores.items():
            for k, v in s.items():
                totals.setdefault(item["type"], {}).setdefault(name, {}).setdefault(k, []).append(v)
                totals.setdefault("all", {}).setdefault(name, {}).setdefault(k, []).append(v)
        for i in orders["hybrid"][:10]:
            (rel_cos if relevant[i] else irr_cos).append(float(semantic[i]))
        rows.append((item["query"], item["type"], int(relevant.sum()), scores))

    def fmt(v):
        return "n/a" if np.isnan(v) else f"{v:.2f}"

    lines = ["# Retrieval benchmark", "",
             f"Catalog: {len(catalog.records)} titles, model `{catalog.meta.get('model')}`, built {catalog.meta.get('built_at')}.",
             f"{len(rows)} queries from [`eval/queries.json`](queries.json). Relevance = AniList genre/tag labels "
             "(descriptive queries) or the series name (title queries).", ""]
    for group in ("all", "descriptive", "title"):
        if group not in totals:
            continue
        lines += [f"## {group.capitalize()} queries", "", "| Ranker | P@5 | P@10 | MRR |", "|---|---:|---:|---:|"]
        for name in ("random", "keyword", "semantic", "hybrid"):
            s = totals[group][name]
            bold = "**" if name == "hybrid" else ""
            lines.append(f"| {bold}{name}{bold} | " + " | ".join(fmt(float(np.nanmean(s[k])) if not all(np.isnan(s[k])) else float('nan'))
                                                     for k in ("p5", "p10", "mrr")) + " |")
        lines.append("")
    lines += ["## Can raw similarity label a match?", "",
              f"Cosine of relevant top-10 hits: median {np.median(rel_cos):.3f}, 25th pct {np.percentile(rel_cos, 25):.3f}  ",
              f"Cosine of irrelevant top-10 hits: median {np.median(irr_cos):.3f}, 75th pct {np.percentile(irr_cos, 75):.3f}", "",
              "## Per query (hybrid)", "", "| Query | Type | Relevant titles | P@10 | MRR |", "|---|---|---:|---:|---:|"]
    for query, qtype, n_rel, s in rows:
        lines.append(f"| {query} | {qtype} | {n_rel} | {s['hybrid']['p10']:.1f} | {s['hybrid']['mrr']:.2f} |")
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
