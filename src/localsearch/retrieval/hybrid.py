from __future__ import annotations

from pathlib import Path

from localsearch.retrieval.bm25 import lexical_search
from localsearch.retrieval.semantic import semantic_search


def reciprocal_rank_fusion(*ranked_lists: list[dict], k: int = 60) -> list[dict]:
    fused: dict[str, float] = {}
    seen: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            key = item["path"]
            if key not in seen:
                seen[key] = item
            fused[key] = fused.get(key, 0.0) + (1.0 / (k + rank))

    merged = []
    for path, score in fused.items():
        item = dict(seen[path])
        item["score"] = score
        merged.append(item)

    merged.sort(key=lambda item: item["score"], reverse=True)
    return merged


def hybrid_search(query: str, *, db_path: str | Path = "localsearch.db", limit: int = 10, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
    bm25_results = lexical_search(query, db_path=db_path, limit=50, file_type=file_type, path_filter=path_filter)
    semantic_results = semantic_search(query, db_path=db_path, limit=50, file_type=file_type, path_filter=path_filter)

    fused = reciprocal_rank_fusion(bm25_results, semantic_results)
    return fused[:limit]
