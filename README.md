# ⚡ LONGBOX // Semantic Matrix

A production-grade Vector Search Engine that utilizes localized Transformer Embeddings and multi-objective metadata normalization to execute complex semantic retrieval.

## 🧠 System Architecture

Unlike traditional keyword-search applications, Longbox utilizes Deep Learning and Natural Language Processing (NLP) to map unstructured text into a 384-dimensional mathematical vector space. 

* **Embedding Engine:** `all-MiniLM-L6-v2` (SentenceTransformers)
* **Search Protocol:** Hybrid Cosine Similarity cross-referenced with multidimensional L1 metadata penalty distances.
* **Feature Engineering:** Vectorized metadata extraction mapping qualitative strings (Tone, Scope) to numeric matrices.
* **Frontend:** Streamlit with custom CSS injection and persistent Singleton memory caching.

## 🚀 The Hybrid Scoring Heuristic

Standard Cosine Similarity often produces false positives on vague user prompts. Longbox mitigates this by implementing a **Multi-Objective Optimization Formula**. 

Users define target narrative constraints (e.g., "Grimdark Tone" or "Street-Level Scope"). The engine normalizes the raw NLP semantic scores to a `[0, 1]` range, calculates the L1 distance between the user's constraints and the dataset's engineered features, and applies a weighted mathematical penalty to return a highly accurate Composite Score.

## 🛠️ Local Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment and install dependencies: `pip install -r requirements.txt`
4. Boot the engine: `python -m streamlit run longbox_engine.py`