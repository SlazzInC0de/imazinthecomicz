"""
Offline retrieval evaluation for IMAZINTHECOMICS.

Relevance labels come from catalog metadata: a title is relevant to a query
when its Genre / Publisher / Theme matches the rule in eval/queries.json.
"Paraphrase" queries avoid the genre words on purpose, so they test meaning
rather than keyword overlap.

Compares three rankers on Precision@5, Precision@10 and MRR:
  * random            - expected precision equals the share of relevant titles
  * TF-IDF keywords   - lexical baseline over the same documents
  * semantic engine   - all-MiniLM-L6-v2 cosine similarity (sliders neutral)

Usage:  python eval/evaluate.py [--out eval/results.md]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def relevant_mask(catalog: pd.DataFrame, rule: dict) -> np.ndarray:
    mask = np.zeros(len(catalog), dtype=bool)
    for key, column in (("genre_any", "Genre"), ("publisher_any", "Studio/Publisher"), ("theme_any", "Theme (Color Style)")):
        if key in rule:
            text = catalog[column].astype(str).str.lower()
            for term in rule[key]:
                mask |= text.str.contains(term, regex=False).to_numpy()
    return mask


def metrics(ranked_idx: np.ndarray, relevant: np.ndarray) -> dict:
    hits = relevant[ranked_idx]
    first = np.flatnonzero(hits)
    return {
        "p5": hits[:5].mean(),
        "p10": hits[:10].mean(),
        "mrr": 1.0 / (first[0] + 1) if len(first) else 0.0,
    }


def tfidf_ranker(docs):
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vec.fit_transform(docs)

    def rank(query):
        scores = (matrix @ vec.transform([query]).T).toarray().ravel()
        return np.argsort(-scores, kind="stable")

    return rank


def semantic_ranker(engine):
    def rank(query):
        results = engine.search(query=query, top_k=len(engine.catalog), tone=0.5, scope=0.5)
        return results.index.to_numpy()

    return rank


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "eval", "results.md"))
    args = parser.parse_args()

    from engine import SemanticMatrixEngine

    engine = SemanticMatrixEngine()
    engine.index_catalog(os.path.join(ROOT, "catalog_cache.pkl"), os.path.join(ROOT, "vector_cache.npy"))
    catalog = engine.catalog.reset_index(drop=True)
    engine.catalog = catalog

    with open(os.path.join(ROOT, "eval", "queries.json")) as fh:
        queries = json.load(fh)

    rankers = {
        "TF-IDF keywords": tfidf_ranker(catalog["semantic_doc"].astype(str).tolist()),
        "Semantic engine": semantic_ranker(engine),
    }

    rows = []
    for q in queries:
        relevant = relevant_mask(catalog, q)
        row = {"query": q["query"], "type": q["type"], "relevant": int(relevant.sum()), "random": relevant.mean()}
        for name, rank in rankers.items():
            for metric, value in metrics(rank(q["query"]), relevant).items():
                row[f"{name}|{metric}"] = value
        rows.append(row)
    df = pd.DataFrame(rows)

    def summary(sub):
        out = {"Random (expected)": (sub["random"].mean(), sub["random"].mean(), None)}
        for name in rankers:
            out[name] = (sub[f"{name}|p5"].mean(), sub[f"{name}|p10"].mean(), sub[f"{name}|mrr"].mean())
        return out

    lines = [
        "# Retrieval evaluation",
        "",
        f"{len(queries)} queries over {len(catalog):,} titles. Relevance is defined by catalog metadata "
        "(see `eval/queries.json`); paraphrase queries deliberately avoid the genre words.",
        "Sliders are left neutral (0.5) for the semantic engine.",
        "",
    ]
    for label, sub in (("All queries", df), ("Paraphrase queries only", df[df["type"] == "paraphrase"]), ("Explicit queries only", df[df["type"] == "explicit"])):
        lines += [f"## {label} ({len(sub)})", "", "| Ranker | P@5 | P@10 | MRR |", "|---|---:|---:|---:|"]
        for name, (p5, p10, mrr) in summary(sub).items():
            mrr_s = "n/a" if mrr is None else f"{mrr:.2f}"
            lines.append(f"| {name} | {p5:.2f} | {p10:.2f} | {mrr_s} |")
        lines.append("")

    lines += ["## Per query (P@5)", "", "| Query | Type | Relevant titles | Random | TF-IDF | Semantic |", "|---|---|---:|---:|---:|---:|"]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['query']} | {r['type']} | {r['relevant']:,} | {r['random']:.2f} | "
            f"{r['TF-IDF keywords|p5']:.2f} | {r['Semantic engine|p5']:.2f} |"
        )

    text = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
