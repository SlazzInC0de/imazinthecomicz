"""
test_vibe.py — Smoke-test the production pipeline end-to-end.

This script exercises the SAME code path that the Streamlit app uses:
  1. It loads catalog_cache.pkl and vector_cache.npy (the real cache).
  2. It uses SemanticMatrixEngine from longbox_engine.py (the same class).
  3. It does NOT re-encode the corpus or use different field names.

If this passes, the app will work. If this breaks, the app will break.

Usage:
    python test_vibe.py
    python test_vibe.py --query "cosmic horror featuring Lovecraftian elder gods" --tone 0.9 --scope 0.8
"""

import argparse
import sys

parser = argparse.ArgumentParser(description="Smoke-test the LONGBOX search pipeline.")
parser.add_argument("--catalog",  default="catalog_cache.pkl", help="Path to catalog cache.")
parser.add_argument("--vectors",  default="vector_cache.npy",  help="Path to vector cache.")
parser.add_argument("--query",    default="A dark street-level vigilante fighting organised crime", help="Test query.")
parser.add_argument("--tone",     type=float, default=0.8,  help="Tone slider value (0=campy, 1=grimdark).")
parser.add_argument("--scope",    type=float, default=0.2,  help="Scope slider value (0=street, 1=cosmic).")
parser.add_argument("--top-k",   type=int,   default=5,    help="Number of results to show.")
args = parser.parse_args()

# FIX #10: Import directly from the real engine module, not a divergent reimplementation.
try:
    from longbox_engine import SemanticMatrixEngine
except ImportError as e:
    print(f"❌  Could not import longbox_engine: {e}")
    print("   Make sure you're running this from the same directory as longbox_engine.py")
    sys.exit(1)

print("⚙️   Booting SemanticMatrixEngine...")
engine = SemanticMatrixEngine()

print(f"📂  Loading cache files...")
try:
    # FIX #6: Both paths passed explicitly — matches the fixed index_catalog signature.
    engine.index_catalog(args.catalog, args.vectors)
except SystemExit:
    # st.stop() raises SystemExit in non-Streamlit context; catch it cleanly.
    print("❌  Cache load failed. Run `python build_index.py` first.")
    sys.exit(1)

# FIX #9: No arbitrary row cap — we test against the full catalog.
print(f"    Catalog loaded: {len(engine.catalog):,} comics, {engine.vector_matrix.shape} vectors")
print()

print("=" * 60)
print(f"🔮  QUERY : {args.query!r}")
print(f"    Tone  : {args.tone}  (0=campy → 1=grimdark)")
print(f"    Scope : {args.scope}  (0=street → 1=cosmic)")
print("=" * 60)

results = engine.search(
    query=args.query,
    top_k=args.top_k,
    tone=args.tone,
    scope=args.scope,
)

for rank, (_, row) in enumerate(results.iterrows(), start=1):
    score_pct = f"{row['composite_score'] * 100:.1f}%"
    print(f"\n#{rank}  [{score_pct}]  {row['Title']}")
    print(f"     {row['Studio/Publisher']} ({row['Release Year']})")
    print(f"     Writer: {row['Writer']}  |  Raw NLP: {row['semantic_score']:.3f}")
    print(f"     {row['semantic_doc'][:120]}...")

print("\n✅  Smoke test complete.")