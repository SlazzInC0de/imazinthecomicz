"""Query embeddings. The model must match the one that built data/embeddings.npy."""
import os
from functools import lru_cache
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def embed_query(self, text: str) -> np.ndarray: ...


class FastEmbedder:
    """ONNX runtime model via fastembed: no PyTorch, about 130 MB of RAM."""

    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name, cache_dir=os.environ.get("FASTEMBED_CACHE_PATH"))
        self._cached = lru_cache(maxsize=2048)(self._embed)

    def _embed(self, text: str) -> bytes:
        vector = next(iter(self._model.query_embed([text]))).astype(np.float32)
        vector /= max(float(np.linalg.norm(vector)), 1e-9)
        return vector.tobytes()

    def embed_query(self, text: str) -> np.ndarray:
        return np.frombuffer(self._cached(text.strip().lower()), dtype=np.float32)
