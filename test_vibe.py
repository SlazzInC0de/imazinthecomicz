import pandas as pd
from sentence_transformers import SentenceTransformer, util

df = pd.read_csv("comics.csv")

df = df.fillna('')
df['synthetic_plot'] = df['Title'] + " - A " + df['Genre'] + " comic published by " + df['Studio/Publisher'] + ". Written by " + df['Writer'] + " with " + df['Theme (Color Style)'] + " art."

test_df = df.head(400).copy()

print("Downloading HuggingFace NLP Model (will take ~15 seconds)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Vectorizing comic books...")
corpus_embeddings = model.encode(test_df['synthetic_plot'].astype(str).tolist(), convert_to_tensor=True)

my_vibe = "A dark fantasy comic with traditional ink art"
vibe_embedding = model.encode(my_vibe, convert_to_tensor=True)

hits = util.semantic_search(vibe_embedding, corpus_embeddings, top_k=3)[0]

print(f"\n" + "="*50)
print(f"🔮 VIBE QUERY: '{my_vibe}'")
print("="*50)

for hit in hits:
    match = test_df.iloc[hit['corpus_id']]

    print(f"• [Match: {hit['score']:.2f}] {match['Title']}")
    print(f"  Reason: {match['synthetic_plot']}\n")