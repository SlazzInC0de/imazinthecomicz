# 💥 ImazinTHEComicz // NLP Recommendation Engine

A production-grade AI recommendation engine that utilizes Transformer Embeddings and multi-objective metadata normalization to execute complex semantic retrieval for comic books and graphic novels.

## 🧠 System Architecture
Unlike traditional keyword-search APIs, ImazinTHEComicz uses Deep Learning (NLP) to map unstructured text into a 384-dimensional mathematical vector space. 

* **Embedding Engine:** `all-MiniLM-L6-v2` (SentenceTransformers)
* **Search Protocol:** Hybrid Cosine Similarity cross-referenced with multidimensional L1 metadata penalties.
* **UI & Caching:** Streamlit frontend with Singleton memory caching, custom Neobrutalist CSS injection, and an offline `.npy` indexing script.

## 🚀 The Hybrid Scoring Heuristic
Standard Cosine Similarity often produces false positives. This engine mitigates this via a **Multi-Objective Optimization Formula**. The system normalizes raw NLP semantic scores to a `[0, 1]` range, calculates the distance between the user's vibe constraints and the dataset's engineered features, and applies a weighted penalty to return a highly accurate Composite Match Score.

## 🛠️ Local Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment and install dependencies: `pip install -r requirements.txt`
4. Run the offline indexer: `python build_index.py`
5. Boot the engine: `python -m streamlit run engine.py`