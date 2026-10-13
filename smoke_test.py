"""
smoke_test.py — Smoke-test the IMAZINTHECOMICS production pipeline.

Usage:
    python smoke_test.py
    python smoke_test.py --query "cosmic horror featuring Lovecraftian elder gods" --tone 0.9 --scope 0.8
"""

import argparse
import sys

parser = argparse.ArgumentParser(description="Smoke-test the IMAZINTHECOMICS search pipeline.")
parser.add_argument("--catalog",  default="catalog_cache.pkl", help="Path to catalog cache.")
parser.add_argument("--vectors",  default="vector_cache.npy",  help="Path to vector cache.")
parser.add_argument("--query",    default="A dark street-level vigilante fighting organised crime", help="Test query.")
parser.add_argument("--tone",     type=float, default=0.8,  help="Tone slider value (0=campy, 1=grimdark).")
parser.add_argument("--scope",    type=float, default=0.2,  help="Scope slider value (0=street, 1=cosmic).")
parser.add_argument("--top-k",    type=int,   default=5,    help="Number of results to show.")
args = parser.parse_args()

try:
    from engine import SemanticMatrixEngine
except ImportError as e:
    print(f"❌ Could not import engine: {e}")
    print("   Make sure engine.py is in the same directory.")
    sys.exit(1)

print("⚙️  Booting IMAZINTHECOMICS Engine...")
engine = SemanticMatrixEngine()

print(f"📂 Loading cache files...")
try:
    engine.index_catalog(args.catalog, args.vectors)
except FileNotFoundError as e:
    print(f"❌ Cache load failed: {e}")
    print("   Run your index builder first.")
    sys.exit(1)

print(f"   Catalog loaded: {len(engine.catalog):,} comics, {engine.vector_matrix.shape} vectors")
print()

print("=" * 60)
print(f"🔮 QUERY : {args.query!r}")
print(f"   Tone  : {args.tone}  (0=campy → 1=grimdark)")
print(f"   Scope : {args.scope}  (0=street → 1=cosmic)")
print("=" * 60)

results = engine.search(
    query=args.query,
    top_k=args.top_k,
    tone=args.tone,
    scope=args.scope,
)

for rank, (_, row) in enumerate(results.iterrows(), start=1):
    score_pct = f"{row['composite_score'] * 100:.1f}%"
    print(f"\n#{rank}  [{score_pct}]  {row.get('Title', 'Unknown')}")
    print(f"     {row.get('Studio/Publisher', 'Unknown')} ({row.get('Release Year', 'N/A')})")
    print(f"     Writer: {row.get('Writer', 'Unknown')}  |  Raw NLP: {row['semantic_score']:.3f}")
    doc_preview = str(row.get('semantic_doc', ''))[:120]
    print(f"     {doc_preview}...")

print("\n✅ Smoke test complete.")