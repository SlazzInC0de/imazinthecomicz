"""
build_index.py — Offline pre-computation step.
Run this ONCE to build vector_cache.npy and catalog_cache.pkl.
The Streamlit app loads those cached files at startup and never re-encodes.

Usage:
    python build_index.py --csv comics.csv
"""

import argparse
import sys
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Build the LONGBOX vector index.")
parser.add_argument("--csv", default="comics.csv", help="Path to the comics CSV file.")
parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name.")
parser.add_argument("--out-dir", default=".", help="Directory to write cache files into.")
args = parser.parse_args()

csv_path = Path(args.csv)
out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

if not csv_path.exists():
    print(f"❌  CSV not found: {csv_path}")
    sys.exit(1)

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────

print(f"📂  Loading {csv_path} ...")
df = pd.read_csv(csv_path).fillna("")
print(f"    {len(df):,} rows loaded.")

# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────

print("📊  Engineering features...")

# FIX #1: Richer semantic document — more signal, better search results.
# Old version only used Title + Genre + Writer. We now include publisher, year, and theme.
df["semantic_doc"] = (
    df["Title"]
    + " — "
    + df["Genre"]
    + " comic published by "
    + df["Studio/Publisher"]
    + " ("
    + df["Release Year"].astype(str)
    + "). Written by "
    + df["Writer"]
    + ", art by "
    + df["Artist"]
    + ". Visual style: "
    + df["Theme (Color Style)"]
)

# FIX #2: Graduated tone_vector instead of a binary 0.5/0.9 flag.
# We score how many tone-indicating words appear to get a real gradient.
DARK_WORDS = ["dark", "horror", "crime", "noir", "violence", "grim", "death", "war", "dystopia"]
LIGHT_WORDS = ["campy", "comedy", "humor", "lighthearted", "fun", "kids", "adventure", "whimsical"]

def score_tone(genre_str: str) -> float:
    """Returns a float in [0, 1]: 0 = pure campy, 1 = pure grimdark."""
    g = str(genre_str).lower()
    dark_hits = sum(w in g for w in DARK_WORDS)
    light_hits = sum(w in g for w in LIGHT_WORDS)
    total = dark_hits + light_hits
    if total == 0:
        return 0.5  # Neutral only when there's genuinely no signal
    return dark_hits / total

# FIX #2 (scope): Same graduated approach for street-level vs cosmic scope.
COSMIC_WORDS = ["cosmic", "event", "sci-fi", "space", "multiverse", "galaxy", "interstellar", "epic"]
STREET_WORDS = ["street", "vigilante", "crime", "detective", "urban", "city", "noir", "local"]

def score_scope(genre_str: str) -> float:
    """Returns a float in [0, 1]: 0 = pure street-level, 1 = pure cosmic."""
    g = str(genre_str).lower()
    cosmic_hits = sum(w in g for w in COSMIC_WORDS)
    street_hits = sum(w in g for w in STREET_WORDS)
    total = cosmic_hits + street_hits
    if total == 0:
        return 0.5
    return cosmic_hits / total

df["tone_vector"] = df["Genre"].apply(score_tone)
df["scope_vector"] = df["Genre"].apply(score_scope)

# Diagnostic: show the distribution so you can validate it makes sense
print(f"    tone_vector  — mean: {df['tone_vector'].mean():.3f}, unique values: {df['tone_vector'].nunique()}")
print(f"    scope_vector — mean: {df['scope_vector'].mean():.3f}, unique values: {df['scope_vector'].nunique()}")

# ─────────────────────────────────────────────
# 3. ENCODE EMBEDDINGS
# ─────────────────────────────────────────────

print(f"\n🧠  Loading model '{args.model}' ...")
model = SentenceTransformer(args.model)

print("🔢  Encoding semantic documents (this takes a minute or two)...")
# FIX #3: normalize_embeddings=True makes cosine similarity more accurate
# because dot-product on unit vectors equals cosine similarity exactly.
vectors = model.encode(
    df["semantic_doc"].tolist(),
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,   # ← was missing before
    batch_size=64,
)

print(f"    Vector matrix shape: {vectors.shape}")

# ─────────────────────────────────────────────
# 4. SAVE CACHE
# ─────────────────────────────────────────────

vec_path = out_dir / "vector_cache.npy"
cat_path = out_dir / "catalog_cache.pkl"

print(f"\n💾  Saving cache to '{out_dir}' ...")
np.save(str(vec_path), vectors)
df.to_pickle(str(cat_path))

print(f"\n✅  Done.")
print(f"    {vec_path}  ({vec_path.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"    {cat_path}  ({cat_path.stat().st_size / 1024:.0f} KB)")
print("\nYou can now start the Streamlit app: `streamlit run longbox_engine.py`")