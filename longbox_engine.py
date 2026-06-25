import os
import streamlit as st
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# =====================================================================
# 1. ENTERPRISE ARCHITECTURE: CORE INTERFACES & ENGINES
# =====================================================================

class BaseSearchEngine(ABC):
    @abstractmethod
    def index_catalog(self, data_path: str) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_k: int, **kwargs) -> pd.DataFrame:
        pass

class SemanticMatrixEngine(BaseSearchEngine):
    def __init__(self):
        # We don't load the model here anymore because we are using the pre-computed cache!
        self.catalog: pd.DataFrame = pd.DataFrame()
        self.vector_matrix: np.ndarray = np.array([])

    def index_catalog(self, data_path: str) -> None:
        """Loads the pre-computed catalog and embedding matrix from the offline index."""
        try:
            self.catalog = pd.read_pickle("catalog_cache.pkl")
            self.vector_matrix = np.load("vector_cache.npy")
        except FileNotFoundError:
            st.error("Cache missing! You must run build_index.py first.")
            st.stop()

    def search(self, query: str, top_k: int = 5, **kwargs) -> pd.DataFrame:
        user_tone = kwargs.get('tone', 0.5)
        user_scope = kwargs.get('scope', 0.5)
        
        # We only need the model momentarily to encode the user's specific query
        from sentence_transformers import SentenceTransformer, util
        query_model = SentenceTransformer('all-MiniLM-L6-v2')
        query_vector = query_model.encode(query, convert_to_numpy=True)
        
        semantic_scores = util.cos_sim(query_vector, self.vector_matrix)[0].numpy()
        
        if (semantic_scores.max() - semantic_scores.min()) > 0:
            norm_semantic = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min())
        else:
            norm_semantic = semantic_scores

        tone_penalties = np.abs(self.catalog['tone_vector'].values - user_tone)
        scope_penalties = np.abs(self.catalog['scope_vector'].values - user_scope)
        
        composite_scores = (norm_semantic * 0.70) - (tone_penalties * 0.15) - (scope_penalties * 0.15)
        
        results_df = self.catalog.copy()
        results_df['semantic_score'] = semantic_scores
        results_df['composite_score'] = composite_scores
        
        return results_df.sort_values(by='composite_score', ascending=False).head(top_k)

# =====================================================================
# 2. PERFORMANCE-OPTIMIZED INITIALIZATION LAYER
# =====================================================================

@st.cache_resource
def initialize_production_engine() -> SemanticMatrixEngine:
    engine = SemanticMatrixEngine()
    engine.index_catalog("catalog_cache.pkl") # The argument isn't strictly used in the new method but satisfies the interface
    return engine

# =====================================================================
# 3. STREAMLIT APPLICATION INTERFACE (COMIC BOOK OVERRIDE)
# =====================================================================

st.set_page_config(
    page_title="LONGBOX // Semantic Matrix",
    page_icon="💥",
    layout="wide"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@700&display=swap');

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
        text-shadow: 2px 2px 0px #fff, 4px 4px 0px #000;
    }

    .comic-panel {
        background-color: #fff;
        border: 4px solid #000;
        padding: 20px;
        margin-bottom: 30px;
        position: relative;
        transition: transform 0.2s;
    }
    
    .panel-odd {
        box-shadow: 8px 8px 0px #00bcd4;
        transform: rotate(-0.5deg);
    }
    .panel-even {
        box-shadow: 8px 8px 0px #ff0055;
        transform: rotate(0.5deg);
    }
    
    .comic-panel:hover {
        transform: scale(1.02);
    }

    .pow-badge {
        background-color: #ffe81f;
        border: 3px solid #000;
        padding: 4px 12px;
        font-family: 'Bangers', cursive;
        font-size: 1.4rem;
        position: absolute;
        top: -15px;
        right: -15px;
        transform: rotate(12deg);
        box-shadow: 4px 4px 0px #000;
        color: #000;
    }

    .stSlider > div > div > div > div {background-color: #ff0055 !important;}
    
    .comic-text { font-size: 1.1em; line-height: 1.4; }
    .comic-meta { font-size: 0.9em; background: #000; color: #fff; padding: 2px 6px; font-family: monospace;}
    </style>
""", unsafe_allow_html=True)

st.title("💥 LONGBOX // VECTOR INDEX")
st.markdown("**THE HYBRID SEMANTIC SEARCH ENGINE!**")
st.markdown("---")

try:
    engine = initialize_production_engine()
except Exception as e:
    st.error(f"Engine Core Initialization Failure: {str(e)}")
    st.stop()

col_controls, col_display = st.columns([1, 2], gap="large")

with col_controls:
    st.markdown("### 🎛️ VIBE CONTROLS")
    st.write("Tune the Multiverse Constraints:")
    
    slider_tone = st.slider("Tone (Campy ➡ Grimdark)", 0.0, 1.0, 0.5, 0.05)
    slider_scope = st.slider("Scope (Street ➡ Cosmic)", 0.0, 1.0, 0.5, 0.05)
    
    st.markdown("---")
    st.markdown("### 🕵️‍♂️ TECH SPECS")
    st.markdown("""
    **Model:** `all-MiniLM-L6-v2`  
    **Architecture:** Hybrid Cosine Similarity + L1 Penalty  
    **UI:** CSS Grid Neobrutalism
    """)

with col_display:
    st.markdown("### 💭 WHAT ARE YOU LOOKING FOR?")
    user_query = st.text_input(
        "Type your hyper-specific vibe here...", 
        placeholder="e.g., A street-level vigilante fighting mobsters..."
    )
    
    if user_query:
        with st.spinner("BAM! Calculating vectors..."):
            results = engine.search(
                query=user_query, 
                top_k=5, 
                tone=slider_tone, 
                scope=slider_scope
            )
            
        st.markdown("### 📚 THE ARCHIVES SAY...")
        
        for idx, row in enumerate(results.iterrows()):
            data = row[1]
            panel_class = "panel-odd" if idx % 2 == 0 else "panel-even"
            
            st.markdown(f"""
            <div class="comic-panel {panel_class}">
                <div class="pow-badge">MATCH: {data['composite_score']:.2f}</div>
                <h2 style="margin: 0;">{data['Title']}</h2>
                <p style="margin: 5px 0;">
                    <span class="comic-meta">WRITER: {data['Writer']}</span> 
                    <span class="comic-meta">ARTIST: {data['Artist']}</span>
                </p>
                <div style="background-color: #fdfdf9; border: 2px solid #000; padding: 10px; margin-top: 10px;">
                    <p class="comic-text"><em>"{data['semantic_doc']}"</em></p>
                </div>
                <p style="margin-top: 10px; font-size: 0.8em; color: #555;">
                    PUBLISHER: <strong>{data['Studio/Publisher']} ({data['Release Year']})</strong> | Raw NLP Score: {data['semantic_score']:.3f}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("System standby. Awaiting query...")