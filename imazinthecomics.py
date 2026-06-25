import os
import html as html_lib
import traceback
import streamlit as st
from engine import SemanticMatrixEngine

# =====================================================================
# 1. SETUP & CACHING
# =====================================================================

CATALOG_PATH = os.environ.get("IMAZIN_CATALOG", "catalog_cache.pkl")
VECTOR_PATH = os.environ.get("IMAZIN_VECTORS", "vector_cache.npy")

@st.cache_resource(show_spinner=False)
def initialize_engine():
    """Load model + cache exactly once per Streamlit process."""
    engine = SemanticMatrixEngine()
    engine.index_catalog(CATALOG_PATH, VECTOR_PATH)
    return engine

def safe(value) -> str:
    """HTML-escape a DataFrame cell value before injecting into markup."""
    return html_lib.escape(str(value))

# =====================================================================
# 2. STREAMLIT UI & STYLING
# =====================================================================

st.set_page_config(
    page_title="IMAZINTHECOMICS",
    page_icon="🦸",
    layout="wide",
)

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
hr {
    border: none;
    border-top: 3px solid #000 !important;
    margin: 1rem 0 !important;
}
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
[data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background-color: #ff0055 !important;
}
[data-baseweb="slider"] [role="slider"] {
    background-color: #ff0055 !important;
    border-color: #ff0055 !important;
}
.comic-text { font-size: 1.1em; line-height: 1.5; margin: 0; }
.comic-meta {
    font-size: 0.85em; background: #000; color: #fff; padding: 2px 7px;
    font-family: monospace; display: inline-block; margin-right: 4px; margin-top: 4px;
}
.comic-panel h2 { margin: 0 0 8px 0 !important; }
.results-area { min-height: 200px; }
/* --- FIX INVISIBLE TEXT ON LIGHT BACKGROUND --- */
/* Target slider labels and standard text */
[data-testid="stWidgetLabel"] p, 
[data-testid="stWidgetLabel"] span, 
[data-testid="stMarkdownContainer"] p,
[data-testid="stText"] {
    color: #000000 !important;
    font-family: 'Comic Neue', cursive !important;
    font-weight: 700 !important;
}

/* Target the little numbers above the slider thumb */
[data-baseweb="slider"] div {
    color: #000000 !important;
}

/* Ensure the text input box has black text when typing */
input[type="text"] {
    color: #000000 !important;
    background-color: #ffffff !important;
    border: 2px solid #000000 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🦸 IMAZINTHECOMICS // VECTOR INDEX")
st.markdown("**THE AI-POWERED COMIC RECOMMENDATION ENGINE!**")
st.markdown('<hr>', unsafe_allow_html=True)

# Safe Engine Booting
with st.spinner("⚡ Booting engine..."):
    try:
        engine = initialize_engine()
    except Exception as exc:
        st.error("Engine initialisation failed. See full diagnostics below:")
        st.exception(traceback.format_exc())
        st.stop()

col_controls, col_display = st.columns([1, 2], gap="large")

with col_controls:
    st.markdown("### 🎛️ VIBE CONTROLS")
    st.write("Tune the Multiverse Constraints:")

    slider_tone = st.slider("Tone (Campy ➡ Grimdark)", 0.0, 1.0, 0.5, 0.05)
    slider_scope = st.slider("Scope (Street ➡ Cosmic)", 0.0, 1.0, 0.5, 0.05)

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown("### 🕵️‍♂️ TECH SPECS")
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

            st.markdown(f"""
<div class="comic-panel {panel_class}">
    <div class="pow-badge">MATCH: {score_pct}</div>
    <h2>{safe(row['Title'])}</h2>
    <p style="margin: 4px 0 10px;">
        <span class="comic-meta">WRITER: {safe(row.get('Writer', 'Unknown'))}</span>
        <span class="comic-meta">ARTIST: {safe(row.get('Artist', 'Unknown'))}</span>
    </p>
    <div style="background-color:#fdfdf9; border: 2px solid #000; padding: 10px;">
        <p class="comic-text"><em>{safe(row.get('semantic_doc', 'No description available.'))}</em></p>
    </div>
    <p style="margin-top: 10px; font-size: 0.8em; color: #555;">
        PUBLISHER: <strong>{safe(row.get('Studio/Publisher', 'Unknown'))} ({safe(row.get('Release Year', 'N/A'))})</strong>
        &nbsp;|&nbsp; Raw NLP: {row['semantic_score']:.3f}
    </p>
</div>
""", unsafe_allow_html=True)

    else:
        st.info("System standby. Awaiting query input...")

    st.markdown('</div>', unsafe_allow_html=True)