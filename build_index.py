"""
Build the IMAZINTHECOMICS vector index.
"""
import os
import pickle
import numpy as np
from engine import SemanticMatrixEngine

def build_pipeline():
    print("📦 Starting IMAZINTHECOMICS index generation pipeline...")
    
    catalog_path = os.environ.get("IMAZIN_CATALOG", "catalog_cache.pkl")
    vector_path = os.environ.get("IMAZIN_VECTORS", "vector_cache.npy")
    
    # MOCK DATA - Replace this with your actual Pandas DataFrame/CSV loading logic
    import pandas as pd
    mock_catalog = pd.DataFrame([
        {"Title": "Batman: Year One", "Writer": "Frank Miller", "Artist": "David Mazzucchelli", "Studio/Publisher": "DC", "Release Year": "1987", "semantic_doc": "A gritty, down-to-earth take on Bruce Wayne's first year.", "tone_vector": 0.9, "scope_vector": 0.1},
        {"Title": "Watchmen", "Writer": "Alan Moore", "Artist": "Dave Gibbons", "Studio/Publisher": "DC", "Release Year": "1986", "semantic_doc": "A complex, philosophical deconstruction of superhero tropes.", "tone_vector": 0.8, "scope_vector": 0.5},
    ])
    
    print(f"✨ Processing {len(mock_catalog)} comic entries...")
    engine = SemanticMatrixEngine(model_name="all-MiniLM-L6-v2")
    
    # Compute embeddings
    descriptions = mock_catalog["semantic_doc"].tolist()
    vectors = engine._model.encode(descriptions, show_progress_bar=True)
    
    # Save files
    mock_catalog.to_pickle(catalog_path)
    np.save(vector_path, np.array(vectors))
    print(f"💾 Successfully cached catalog to '{catalog_path}' and vectors to '{vector_path}'.")

if __name__ == "__main__":
    build_pipeline()