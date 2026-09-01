from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import numpy as np


class VectorStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(Path(db_path).expanduser())
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_embeddings (
                    chunk_id INTEGER PRIMARY KEY,
                    vector BLOB NOT NULL,
                    model_name TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def store(self, chunk_id: int, embedding: list[float], model_name: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chunk_embeddings (chunk_id, vector, model_name)
                VALUES (?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    vector = excluded.vector,
                    model_name = excluded.model_name
                """,
                (chunk_id, np.asarray(embedding, dtype=np.float32).tobytes(), model_name),
            )
            conn.commit()

    def get_embedding(self, chunk_id: int) -> list[float] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT vector FROM chunk_embeddings WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
            if row is None:
                return None
            return np.frombuffer(row[0], dtype=np.float32).tolist()

    def all_embeddings(self) -> dict[int, list[float]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT chunk_id, vector FROM chunk_embeddings").fetchall()
            output: dict[int, list[float]] = {}
            for chunk_id, vector in rows:
                output[chunk_id] = np.frombuffer(vector, dtype=np.float32).tolist()
            return output

    def delete_for_chunk(self, chunk_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chunk_embeddings WHERE chunk_id = ?", (chunk_id,))
            conn.commit()
