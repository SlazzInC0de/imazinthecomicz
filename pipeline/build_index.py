"""
Embed every catalog entry and save the matrix next to the catalog.

The same model runs at query time in the API (see api/app/embedder.py), so the
model name is written to data/meta.json and checked when the API starts.

Usage: python pipeline/build_index.py
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

MODEL = "BAAI/bge-small-en-v1.5"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/catalog.parquet")
    parser.add_argument("--out", default="data/embeddings.npy")
    parser.add_argument("--meta", default="data/meta.json")
    parser.add_argument("--batch", type=int, default=128)
    args = parser.parse_args()

    df = pd.read_parquet(args.catalog)
    # Re-embedding 17k titles takes most of an hour; skip it when the text is unchanged.
    digest = hashlib.sha256("\x00".join([MODEL, *df["doc"].tolist()]).encode()).hexdigest()
    if os.path.exists(args.meta) and os.path.exists(args.out):
        with open(args.meta, encoding="utf-8") as fh:
            old = json.load(fh)
        if old.get("docs_sha256") == digest:
            print("Catalog text unchanged, keeping the existing embeddings.")
            return 0

    from fastembed import TextEmbedding

    model = TextEmbedding(MODEL)
    vectors = np.array(list(model.passage_embed(df["doc"].tolist(), batch_size=args.batch)), dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True).clip(min=1e-9)
    # float16 halves the file size; cosine scores move by less than 0.001
    np.save(args.out, vectors.astype(np.float16))

    meta = {
        "model": MODEL,
        "dimensions": int(vectors.shape[1]),
        "titles": int(len(df)),
        "by_kind": {k: int(v) for k, v in df["kind"].value_counts().items()},
        "by_source": {k: int(v) for k, v in df["source"].value_counts().items()},
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "docs_sha256": digest,
    }
    with open(args.meta, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(f"Embedded {len(df)} titles with {MODEL}: {vectors.shape}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
