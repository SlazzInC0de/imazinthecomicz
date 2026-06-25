import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer

class BaseSearchEngine(ABC):
    @abstractmethod
    def index_catalog(self, catalog_path: str, vector_path: str) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_k: int, **kwargs) -> pd.DataFrame:
        pass

class SemanticMatrixEngine(BaseSearchEngine):
    """
    Optimized Multiplicative Search Engine: Text search acts as the gatekeeper,
    while UI sliders act as a 30% contextual fine-tuner.
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
            raise FileNotFoundError(f"Cache file missing: {exc.filename}")

    def search(self, query: str, top_k: int = 5, **kwargs) -> pd.DataFrame:
        user_tone = float(kwargs.get("tone", 0.5))
        user_scope = float(kwargs.get("scope", 0.5))

        # 1. Compute query vector
        query_vector = self._model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # 2. Pure NumPy Cosine Similarity (Eliminates PyTorch list conversion overhead)
        dot_product = np.dot(self.vector_matrix, query_vector)
        matrix_norms = np.linalg.norm(self.vector_matrix, axis=1)
        query_norm = np.linalg.norm(query_vector)
        
        # Prevent division by zero
        matrix_norms[matrix_norms == 0] = 1.0
        query_norm = 1.0 if query_norm == 0 else query_norm
        
        # Raw semantic scores typically fall between -1.0 and 1.0 (mostly > 0 for text)
        semantic_scores = dot_product / (matrix_norms * query_norm)
        
        # Clip negative matches to 0.0 so they don't break percentage math in the UI
        semantic_scores = np.clip(semantic_scores, 0.0, 1.0)

        # 3. Calculate absolute distance penalties [0.0 to 1.0] from sliders
        tone_penalties = np.abs(self.catalog["tone_vector"].values - user_tone)
        scope_penalties = np.abs(self.catalog["scope_vector"].values - user_scope)

        # 4. MULTIPLICATIVE RANKING (The Fix)
        # Sliders can reduce the raw text match score by a maximum of 30% combined (15% each)
        vibe_modifier = 1.0 - (tone_penalties * 0.15 + scope_penalties * 0.15)
        composite_scores = semantic_scores * vibe_modifier

        # 5. Assemble and Sort Results
        results_df = self.catalog.copy()
        results_df["semantic_score"] = semantic_scores
        results_df["composite_score"] = composite_scores

        return results_df.sort_values(by="composite_score", ascending=False).head(top_k)