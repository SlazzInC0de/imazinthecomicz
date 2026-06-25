import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer, util

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
            # Raise a standard Python error, letting the UI decide how to display it
            raise FileNotFoundError(f"Cache file missing: {exc.filename}")

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