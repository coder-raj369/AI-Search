from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path


class LexicalSearchEngine:
    def __init__(self, db_path: str | Path):
        self.db_path = str(Path(db_path).expanduser())

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search(self, query: str, limit: int = 10, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
        if not query.strip():
            return []

        terms = query.strip().split()
        sql_tokens = " ".join(terms)

        with self._connect() as conn:
            tables = []
            for _ in range(1):
                table_name = "fts_chunks"
                tables.append(table_name)
            if not tables:
                return []

            where_clauses = []
            params: list[str] = []
            if file_type:
                where_clauses.append("files.extension = ?")
                params.append(file_type if file_type.startswith(".") else f".{file_type}")
            if path_filter:
                where_clauses.append("files.path LIKE ?")
                params.append(f"%{path_filter}%")

            base_sql = f"""
                SELECT DISTINCT files.path, files.filename, files.extension, files.modified_at, files.size_bytes,
                       files.metadata_json, chunks.content, bm25(fts_chunks) AS score
                FROM fts_chunks
                JOIN chunks ON chunks.id = fts_chunks.rowid
                JOIN files ON files.id = chunks.file_id
                WHERE fts_chunks MATCH ?
            """
            if where_clauses:
                base_sql += " AND " + " AND ".join(where_clauses)
            base_sql += " ORDER BY score DESC LIMIT ?"
            params = [sql_tokens, *params, str(limit)]
            rows = conn.execute(base_sql, params).fetchall()

            query_terms = [token for token in re.findall(r"[A-Za-z0-9_]+", query.lower()) if token]
            results: list[dict] = []
            for row in rows:
                metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                content_text = (row["content"] or "")
                filename_text = (row["filename"] or "")
                full_text = f"{content_text} {filename_text}".lower()
                exact_hits = sum(full_text.count(term) for term in query_terms)
                filename_hits = sum(filename_text.lower().count(term) for term in query_terms)
                unique_hits = sum(1 for term in query_terms if term in full_text)

                score = float(row["score"]) + (exact_hits * 0.2) + (filename_hits * 1.5) + (unique_hits * 0.6)
                results.append(
                    {
                        "path": row["path"],
                        "filename": row["filename"],
                        "extension": row["extension"],
                        "modified_at": row["modified_at"],
                        "size_bytes": row["size_bytes"],
                        "score": score,
                        "snippet": row["content"][:300],
                        "metadata": metadata,
                    }
                )
            return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


def lexical_search(query: str, *, db_path: str | Path = "localsearch.db", limit: int = 10, file_type: str | None = None, path_filter: str | None = None) -> list[dict]:
    engine = LexicalSearchEngine(db_path)
    return engine.search(query, limit=limit, file_type=file_type, path_filter=path_filter)
