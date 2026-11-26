"""Sentence-transformer wrapper used for semantic part matching."""
from __future__ import annotations

from typing import Sequence


class SentenceEmbedder:
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name or self.MODEL_NAME, device="cpu")

    def encode(self, texts: Sequence[str]):
        return self._model.encode(list(texts), normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False)
