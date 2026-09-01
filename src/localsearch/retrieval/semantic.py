from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np

from localsearch.embeddings.model import EmbeddingModel
from localsearch.embeddings.vector_store import VectorStore


class SemanticSearchEngine:
    def __init__(self, db_path: str | Path, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = str(Path(db_path).expanduser())
        self.model = EmbeddingModel(model_name=model_name)
        self.vector_store = VectorStore(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_chunks(self, *, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
        with self._connect() as conn:
            sql = """
                SELECT chunks.id, chunks.file_id, chunks.content, files.path, files.filename, files.extension, files.metadata_json
                FROM chunks
                JOIN files ON files.id = chunks.file_id
            """
            where: list[str] = []
            params: list[str] = []
            if file_type:
                where.append("files.extension = ?")
                params.append(file_type if file_type.startswith(".") else f".{file_type}")
            if path_filter:
                where.append("files.path LIKE ?")
                params.append(f"%{path_filter}%")
            if where:
                sql += " WHERE " + " AND ".join(where)
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 10, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
        if not query.strip():
            return []

        try:
            query_vector = self.model.encode([query])[0]
        except RuntimeError:
            return []

        chunks = self._get_chunks(file_type=file_type, path_filter=path_filter)
        if not chunks:
            return []

        scored: list[dict] = []
        for chunk in chunks:
            chunk_vector = self.vector_store.get_embedding(int(chunk["id"]))
            if chunk_vector is None:
                # Lazy embedding generation for new chunks
                embeddings = self.model.encode([chunk["content"]])
                vector = embeddings[0]
                self.vector_store.store(int(chunk["id"]), vector, self.model.model_name)
                chunk_vector = vector

            similarity = float(np.dot(np.asarray(query_vector, dtype=np.float32), np.asarray(chunk_vector, dtype=np.float32)))
            if similarity <= 0:
                continue

            metadata = json.loads(chunk["metadata_json"]) if chunk["metadata_json"] else {}
            scored.append(
                {
                    "path": chunk["path"],
                    "filename": chunk["filename"],
                    "extension": chunk["extension"],
                    "score": similarity,
                    "snippet": chunk["content"][:300],
                    "metadata": metadata,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]


def semantic_search(query: str, *, db_path: str | Path = "localsearch.db", limit: int = 10, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
    engine = SemanticSearchEngine(db_path)
    return engine.search(query, limit=limit, file_type=file_type, path_filter=path_filter)
