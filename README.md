<div align="center">

# 🦸 IMAZINTHECOMICS

### Semantic comic recommendation engine

**Describe the story you want in plain English. Tune the vibe. Get matching comics.**

[![Tests](https://github.com/SlazzInC0de/imazinthecomicz/actions/workflows/tests.yml/badge.svg)](https://github.com/SlazzInC0de/imazinthecomicz/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-0f172a?logo=python&logoColor=3776AB)
![Sentence Transformers](https://img.shields.io/badge/all--MiniLM--L6--v2-0f172a?logo=huggingface&logoColor=FFD21E)
![Streamlit](https://img.shields.io/badge/Streamlit-0f172a?logo=streamlit&logoColor=FF4B4B)
![NumPy](https://img.shields.io/badge/NumPy-0f172a?logo=numpy&logoColor=4DABCF)
![License](https://img.shields.io/badge/License-MIT-22d3ee)

</div>

---

## ✨ What it does

Keyword search fails on queries like *"a blind lawyer fighting crime in Hell's Kitchen"*. IMAZINTHECOMICS embeds every title in a **10,000-comic catalog** into a 384-dimensional vector space and ranks by meaning, then lets you steer results with two **vibe sliders**:

- 🎭 **Tone**: campy ➡ grimdark
- 🌌 **Scope**: street-level ➡ cosmic

All of it runs locally with a pre-built index, wrapped in a hand-styled, comic-panel Streamlit UI.

## 🧠 How ranking works

```mermaid
flowchart LR
    Q([User query]) --> E[all-MiniLM-L6-v2<br/>query embedding]
    E --> C[Cosine similarity<br/>vs 10k x 384 matrix]
    C --> S[Semantic score<br/>clipped to 0..1]
    T([Tone + Scope sliders]) --> P[Distance to each title's<br/>tone / scope features]
    S --> M{{"composite = semantic x (1 - 0.15·Δtone - 0.15·Δscope)"}}
    P --> M
    M --> R([Top-5 comic panels])
```

- **Text is the gatekeeper.** The semantic score decides what is relevant.
- **Vibe is the fine-tuner.** Sliders can lower a match by at most 30% combined, so they reorder close results without overriding meaning.
- **Tone and scope are derived from metadata** (`vibe.py`): genre keywords plus age rating map each title into [0, 1]. For example, *Horror / Supernatural* lands at tone 0.85, scope 0.70, while *Comedy / Slice of Life* sits at tone 0.00, scope 0.20.

## ⚡ Engineering notes

- **Offline indexing**: `build_index.py` turns catalog metadata into a descriptive document per title, embeds all 10k once and caches `vector_cache.npy` + `catalog_cache.pkl`.
- **Pure NumPy retrieval**: similarity is a single matrix-vector product, with no per-query PyTorch tensor conversion.
- **Load once**: `st.cache_resource` keeps the model and matrix in memory across reruns.
- **Safe rendering**: every catalog value is HTML-escaped before it is injected into the custom panel markup.
- **Tested without the model**: the pytest suite stubs the encoder, so ranking logic runs in CI in under a second.

## 🚀 Run locally

```bash
git clone https://github.com/SlazzInC0de/imazinthecomicz.git
cd imazinthecomicz
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run imazinthecomics.py
```

The prebuilt index ships with the repo. To rebuild it after editing `comics.csv`:

```bash
python build_index.py
```

**CLI smoke test**

```bash
python smoke_test.py --query "cosmic horror with elder gods" --tone 0.9 --scope 0.8
```

**Unit tests**

```bash
pip install pytest
pytest -v
```

## 🗂️ Dataset

`comics.csv` is a **synthetic catalog** of 10,000 titles (manga, manhua, webtoons, Western comics) with writer, artist, publisher, year, format, color style, genre, age rating, page count and more. It exists to exercise the retrieval pipeline at a realistic scale.

## 📁 Project structure

```text
imazinthecomicz/
├── imazinthecomics.py   # Streamlit app (UI + styling)
├── engine.py            # SemanticMatrixEngine: load index, rank queries
├── vibe.py              # Tone / scope feature derivation
├── build_index.py       # Offline embedding + cache builder
├── smoke_test.py        # CLI query runner
├── tests/               # pytest suite (model stubbed)
├── comics.csv           # 10k-title catalog
├── catalog_cache.pkl    # Prebuilt catalog with features
└── vector_cache.npy     # Prebuilt 10k x 384 embeddings
```

## 🗺️ Roadmap

- [ ] Deploy on Streamlit Community Cloud
- [ ] Learn tone and scope from plot summaries instead of metadata rules
- [ ] Filters for format, language and age rating
- [ ] FAISS index for catalogs beyond 100k titles

## 📄 License

MIT © [Suryansh Verma](https://github.com/SlazzInC0de)
