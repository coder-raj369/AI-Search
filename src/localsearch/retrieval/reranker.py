from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class LocalReranker:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name
        self._model: Any = None

    def _load_model(self) -> Any:
        if not self.model_name:
            return None
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError:
                return None
            self._model = CrossEncoder(self.model_name, max_length=512)
        return self._model

    def score(self, query: str, candidates: list[dict]) -> list[float] | None:
        model = self._load_model()
        if model is None:
            return None
        pairs = [(query, candidate.get("snippet", "")) for candidate in candidates]
        return [float(value) for value in model.predict(pairs)]


def _evidence(query: str, candidate: dict) -> list[str]:
    terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
    content = f"{candidate.get('filename', '')} {candidate.get('snippet', '')}".lower()
    matched_terms = [term for term in terms if term in content]
    evidence: list[str] = []
    if matched_terms:
        evidence.append("Exact terms: " + ", ".join(sorted(matched_terms)))
    extension = candidate.get("extension")
    if extension:
        evidence.append(f"File type: {extension}")
    metadata = candidate.get("metadata") or {}
    if metadata.get("language"):
        evidence.append(f"Language: {metadata['language']}")
    if not evidence:
        evidence.append("Retrieved from the indexed content")
    return evidence


def rerank_results(query: str, candidates: list[dict], *, model_name: str | None = None) -> list[dict]:
    if not candidates:
        return []

    reranker = LocalReranker(model_name=model_name)
    neural_scores = reranker.score(query, candidates)
    query_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
    ranked: list[dict] = []

    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if neural_scores is not None:
            score = neural_scores[index]
        else:
            text = f"{item.get('filename', '')} {item.get('snippet', '')}".lower()
            matched_terms = sum(term in text for term in query_terms)
            score = float(item.get("score", 0.0)) + matched_terms / max(len(query_terms), 1)
        item["rerank_score"] = float(score)
        item["why_matched"] = _evidence(query, item)
        ranked.append(item)

    ranked.sort(key=lambda result: result["rerank_score"], reverse=True)
    return ranked
