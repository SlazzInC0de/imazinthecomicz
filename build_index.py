"""
Build the IMAZINTHECOMICS vector index from a real CSV.
"""
import os
import pandas as pd
import numpy as np
from engine import SemanticMatrixEngine
from vibe import add_vibe_features

def build_pipeline():
    print("📦 Starting IMAZINTHECOMICS index generation pipeline...")
    
    catalog_path = os.environ.get("IMAZIN_CATALOG", "catalog_cache.pkl")
    vector_path = os.environ.get("IMAZIN_VECTORS", "vector_cache.npy")
    
    print("📂 Loading database from comics.csv...")
    try:
        catalog = pd.read_csv("comics.csv")
    except FileNotFoundError:
        print("❌ Error: Could not find 'comics.csv'. Make sure the file is in the same folder!")
        return
        
    # ---------------------------------------------------------
    # MAGIC FIX: GENERATING SYNTHETIC DESCRIPTIONS
    # ---------------------------------------------------------
    print("🪄 Generating synthetic semantic descriptions from metadata...")
    
    # Clean up empty cells to prevent 'nan' showing up in the text
    catalog.fillna("Unknown", inplace=True)
    
    # This stitches your specific columns into a readable paragraph for the AI
    def build_description(row):
        genre = row.get('Genre', 'Unknown')
        title = row.get('Title', 'Unknown')
        writer = row.get('Writer', 'Unknown')
        artist = row.get('Artist', 'Unknown')
        publisher = row.get('Studio/Publisher', 'Unknown')
        theme = row.get('Theme (Color Style)', 'Unknown')
        
        return f"A {genre} comic titled '{title}', written by {writer} and illustrated by {artist}. Published by {publisher}. Visual theme: {theme}."

    # Apply the function to create our required 'semantic_doc' column
    catalog['semantic_doc'] = catalog.apply(build_description, axis=1)
    # ---------------------------------------------------------

    # Derive tone (campy -> grimdark) and scope (street -> cosmic) from genre + age rating
    catalog = add_vibe_features(catalog)
        
    print(f"✨ Processing {len(catalog)} comic entries... (This might take a minute for 2000+ rows!)")
    engine = SemanticMatrixEngine(model_name="all-MiniLM-L6-v2")
    
    # Compute embeddings for all generated descriptions
    descriptions = catalog["semantic_doc"].tolist()
    vectors = engine._model.encode(descriptions, show_progress_bar=True)
    
    # Save the new massive database to the cache files
    catalog.to_pickle(catalog_path)
    np.save(vector_path, np.array(vectors))
    print(f"💾 Successfully cached {len(catalog)} comics to '{catalog_path}' and '{vector_path}'.")

if __name__ == "__main__":
    build_pipeline()