import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

print("⚙️ Booting up Offline Indexer...")

# 1. Load the data & Model
df = pd.read_csv("comics.csv").fillna('')
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Feature Engineering (Same as before)
print("📊 Processing metadata...")
df['semantic_doc'] = df['Title'] + " - " + df['Genre'] + " by " + df['Writer']
df['tone_vector'] = df['Genre'].apply(lambda g: 0.9 if any(w in str(g).lower() for w in ['dark', 'horror', 'crime']) else 0.5)
df['scope_vector'] = df['Genre'].apply(lambda g: 0.9 if any(w in str(g).lower() for w in ['cosmic', 'event', 'sci-fi']) else 0.5)

# 3. THE HEAVY LIFTING (Crunching the vectors)
print("🧠 Crunching Neural Embeddings (This will take a minute or two...)")
vectors = model.encode(df['semantic_doc'].tolist(), show_progress_bar=True, convert_to_numpy=True)

# 4. SAVE IT TO THE HARD DRIVE
print("💾 Saving pre-computed matrices to disk...")
np.save("vector_cache.npy", vectors)
df.to_pickle("catalog_cache.pkl")

print("✅ DONE! You can now boot your web app instantly.")