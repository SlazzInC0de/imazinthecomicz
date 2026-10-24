"""Embedding backends. The real one loads sentence-transformers lazily so the
API and tests can run with a lightweight hashing embedder."""
import hashlib
import os

import numpy as np

MODEL_NAME = os.environ.get("IMAZIN_MODEL", "all-MiniLM-L6-v2")


class SentenceEmbedder:
    def __init__(self, model_name: str = MODEL_NAME):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.name = model_name

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=len(texts) > 100).astype(np.float32)


class HashingEmbedder:
    """Deterministic bag-of-words embedder for tests and offline smoke runs."""

    name = "hashing"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in text.lower().split():
                tok = tok.strip(".,:;()'\"!?")
                if tok:
                    out[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


def get_embedder():
    if os.environ.get("IMAZIN_EMBEDDER") == "hashing":
        return HashingEmbedder()
    return SentenceEmbedder()
