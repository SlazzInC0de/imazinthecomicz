"""
longbox_engine.py — LONGBOX // Semantic Matrix Search Engine
Streamlit app. Requires vector_cache.npy and catalog_cache.pkl
produced by build_index.py.

Usage:
    streamlit run longbox_engine.py
"""

import os
import html as html_lib
import numpy as np
import pandas as pd
import streamlit as st
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer, util


# =====================================================================
# 1. CORE INTERFACES
# =====================================================================

class BaseSearchEngine(ABC):
    @abstractmethod
    def index_catalog(self, catalog_path: str, vector_path: str) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_k: int, **kwargs) -> pd.DataFrame:
        pass


class SemanticMatrixEngine(BaseSearchEngine):
    """
    Hybrid search engine: 70% dense semantic similarity + 30% L1 vibe penalty.
    The model is loaded ONCE at __init__ and reused for all queries.
    The catalog and vector matrix are loaded via index_catalog().
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)
        self.catalog: pd.DataFrame = pd.DataFrame()
        self.vector_matrix: np.ndarray = np.array([])

    def index_catalog(self, catalog_path: str, vector_path: str) -> None:
        """Load pre-computed catalog and embedding matrix from disk."""
        try:
            self.catalog = pd.read_pickle(catalog_path)
            self.vector_matrix = np.load(vector_path)
        except FileNotFoundError as exc:
            st.error(
                f"Cache file missing: **{exc.filename}**\n\n"
                "Run `python build_index.py` to generate it, then restart this app."
            )
            st.stop()

    def search(self, query: str, top_k: int = 5, **kwargs) -> pd.DataFrame:
        user_tone = float(kwargs.get("tone", 0.5))
        user_scope = float(kwargs.get("scope", 0.5))

        query_vector = self._model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        raw_scores = util.cos_sim(query_vector, self.vector_matrix)
        semantic_scores = np.array(raw_scores[0].tolist(), dtype=np.float32)

        s_min, s_max = semantic_scores.min(), semantic_scores.max()
        if (s_max - s_min) > 1e-9:
            norm_semantic = (semantic_scores - s_min) / (s_max - s_min)
        else:
            norm_semantic = np.ones_like(semantic_scores) * 0.5

        tone_penalties = np.abs(self.catalog["tone_vector"].values - user_tone)
        scope_penalties = np.abs(self.catalog["scope_vector"].values - user_scope)

        raw_composite = (
            norm_semantic * 0.70
            - tone_penalties * 0.15
            - scope_penalties * 0.15
        )

        c_min, c_max = raw_composite.min(), raw_composite.max()
        if (c_max - c_min) > 1e-9:
            composite_scores = (raw_composite - c_min) / (c_max - c_min)
        else:
            composite_scores = np.ones_like(raw_composite) * 0.5

        results_df = self.catalog.copy()
        results_df["semantic_score"] = semantic_scores
        results_df["composite_score"] = composite_scores

        return results_df.sort_values(by="composite_score", ascending=False).head(top_k)


# =====================================================================
# 2. CACHED INITIALISATION
# =====================================================================

CATALOG_PATH = os.environ.get("LONGBOX_CATALOG", "catalog_cache.pkl")
VECTOR_PATH = os.environ.get("LONGBOX_VECTORS", "vector_cache.npy")


@st.cache_resource
def initialize_engine() -> SemanticMatrixEngine:
    """Load model + cache exactly once per Streamlit process."""
    engine = SemanticMatrixEngine()
    engine.index_catalog(CATALOG_PATH, VECTOR_PATH)
    return engine


# =====================================================================
# 3. HELPERS
# =====================================================================

def safe(value) -> str:
    """HTML-escape a DataFrame cell value before injecting into markup."""
    return html_lib.escape(str(value))


# =====================================================================
# 4. STREAMLIT UI
# =====================================================================

st.set_page_config(
    page_title="LONGBOX // Semantic Matrix",
    page_icon="💥",
    layout="wide",
)

# UI FIX #7: Font loaded as a proper <link> tag injected into the head,
# not as @import inside a <style> block. @import inside injected styles
# is lowest priority and frequently never resolves on slow connections.
st.markdown(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@700&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.stApp {
    background-color: #fdfdf9;
    background-image: radial-gradient(circle, #d5d5d5 1.5px, transparent 1.5px);
    background-size: 10px 10px;
    color: #000;
    font-family: 'Comic Neue', cursive !important;
}

h1, h2, h3 {
    font-family: 'Bangers', cursive !important;
    letter-spacing: 2px;
    color: #000 !important;
    text-transform: uppercase;
    text-shadow: 2px 2px 0 #fff, 4px 4px 0 #000;
}

/* UI FIX #8: Visible divider — dotted background makes <hr> invisible.
   Override with a solid black rule that actually shows up. */
hr {
    border: none;
    border-top: 3px solid #000 !important;
    margin: 1rem 0 !important;
}

/* UI FIX #2: overflow:visible so the absolutely-positioned badge
   isn't clipped by the panel's own box. padding-top makes room for it. */
.comic-panel {
    background-color: #fff;
    border: 4px solid #000;
    padding: 28px 20px 20px 20px;
    margin-top: 20px;
    margin-bottom: 30px;
    position: relative;
    overflow: visible;
    transition: transform 0.2s;
}

/* UI FIX #1: hover must carry the rotation PLUS the scale.
   A plain `transform: scale(1.02)` overwrites the rotate — so each
   variant needs its own :hover rule that combines both transforms. */
.panel-odd {
    box-shadow: 8px 8px 0 #00bcd4;
    transform: rotate(-0.5deg);
}
.panel-even {
    box-shadow: 8px 8px 0 #ff0055;
    transform: rotate(0.5deg);
}
.panel-odd:hover  { transform: rotate(-0.5deg) scale(1.02); }
.panel-even:hover { transform: rotate(0.5deg)  scale(1.02); }

/* UI FIX #6: z-index so badge always renders on top of sibling panels. */
.pow-badge {
    background-color: #ffe81f;
    border: 3px solid #000;
    padding: 4px 12px;
    font-family: 'Bangers', cursive;
    font-size: 1.4rem;
    position: absolute;
    top: -18px;
    right: -12px;
    transform: rotate(12deg);
    box-shadow: 4px 4px 0 #000;
    color: #000;
    z-index: 10;
    white-space: nowrap;
}

/* UI FIX #4: Target the actual Streamlit/BaseWeb slider track element.
   The old deep-child selector (.stSlider > div > div > div > div) was
   fragile and broke on most Streamlit versions. */
[data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background-color: #ff0055 !important;
}
[data-baseweb="slider"] [role="slider"] {
    background-color: #ff0055 !important;
    border-color: #ff0055 !important;
}

.comic-text {
    font-size: 1.1em;
    line-height: 1.5;
    margin: 0;
}

.comic-meta {
    font-size: 0.85em;
    background: #000;
    color: #fff;
    padding: 2px 7px;
    font-family: monospace;
    display: inline-block;
    margin-right: 4px;
    margin-top: 4px;
}

/* UI FIX #5: Explicit margin-bottom on the title so it never sits
   flush against the meta line regardless of Streamlit's heading reset. */
.comic-panel h2 {
    margin: 0 0 8px 0 !important;
}

/* UI FIX #10: Reserve space so the page doesn't jump when results load. */
.results-area {
    min-height: 200px;
}
</style>
""", unsafe_allow_html=True)

st.title("💥 LONGBOX // VECTOR INDEX")
st.markdown("**THE HYBRID SEMANTIC SEARCH ENGINE!**")

# UI FIX #8: Custom <hr> instead of st.markdown("---") which renders
# an invisible rule against the dotted background.
st.markdown('<hr>', unsafe_allow_html=True)

with st.spinner("⚡ Booting engine..."):
    try:
        engine = initialize_engine()
    except Exception as exc:
        st.error(f"Engine initialisation failed: {exc}")
        st.stop()

col_controls, col_display = st.columns([1, 2], gap="large")

with col_controls:
    st.markdown("### 🎛️ VIBE CONTROLS")
    st.write("Tune the Multiverse Constraints:")

    slider_tone = st.slider("Tone (Campy ➡ Grimdark)", 0.0, 1.0, 0.5, 0.05)
    slider_scope = st.slider("Scope (Street ➡ Cosmic)", 0.0, 1.0, 0.5, 0.05)

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown("### 🕵️‍♂️ TECH SPECS")
    # UI FIX #9: Stripped trailing whitespace before closing triple-quote.
    st.markdown(
        "**Model:** `all-MiniLM-L6-v2`\n\n"
        "**Architecture:** Hybrid Cosine + L1 Vibe Penalty\n\n"
        "**Scoring:** Normalised composite [0 → 1]\n\n"
        "**Catalog:** `catalog_cache.pkl`"
    )

with col_display:
    st.markdown("### 💭 WHAT ARE YOU LOOKING FOR?")
    user_query = st.text_input(
        "Type your hyper-specific vibe here...",
        placeholder="e.g., A street-level vigilante fighting organised crime in a neon-lit city...",
    )

    st.markdown('<div class="results-area">', unsafe_allow_html=True)

    if user_query:
        with st.spinner("BAM! Calculating vectors..."):
            results = engine.search(
                query=user_query,
                top_k=5,
                tone=slider_tone,
                scope=slider_scope,
            )

        st.markdown("### 📚 THE ARCHIVES SAY...")

        for idx, (_, row) in enumerate(results.iterrows()):
            panel_class = "panel-odd" if idx % 2 == 0 else "panel-even"
            score_pct = f"{row['composite_score'] * 100:.0f}%"

            # UI FIX #3: Every cell from the DataFrame is HTML-escaped before
            # injection. A title like <script>alert(1)</script> previously
            # executed. Now it renders as safe visible text.
            st.markdown(f"""
<div class="comic-panel {panel_class}">
    <div class="pow-badge">MATCH: {score_pct}</div>
    <h2>{safe(row['Title'])}</h2>
    <p style="margin: 4px 0 10px;">
        <span class="comic-meta">WRITER: {safe(row['Writer'])}</span>
        <span class="comic-meta">ARTIST: {safe(row['Artist'])}</span>
    </p>
    <div style="background-color:#fdfdf9; border: 2px solid #000; padding: 10px;">
        <p class="comic-text"><em>{safe(row['semantic_doc'])}</em></p>
    </div>
    <p style="margin-top: 10px; font-size: 0.8em; color: #555;">
        PUBLISHER: <strong>{safe(row['Studio/Publisher'])} ({safe(row['Release Year'])})</strong>
        &nbsp;|&nbsp; Raw NLP: {row['semantic_score']:.3f}
    </p>
</div>
""", unsafe_allow_html=True)

    else:
        st.info("System standby. Awaiting query input...")

    st.markdown('</div>', unsafe_allow_html=True)