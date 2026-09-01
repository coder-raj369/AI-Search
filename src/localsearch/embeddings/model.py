from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EmbeddingModel:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"

    def encode(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("sentence-transformers is required for semantic search") from exc

        model = SentenceTransformer(self.model_name, device=self.device)
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype(float).tolist()
