from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class DatabaseManager:
    def __init__(self, db_path: str | Path):
        self.db_path = str(Path(db_path).expanduser())
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    extension TEXT,
                    size_bytes INTEGER,
                    modified_at TEXT,
                    hash TEXT,
                    mime_type TEXT,
                    indexed_at TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    cell_number INTEGER,
                    metadata_json TEXT,
                    FOREIGN KEY(file_id) REFERENCES files(id)
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                    content, file_id UNINDEXED, file_path UNINDEXED, filename UNINDEXED, tokenize='porter unicode61'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            conn.commit()

    def insert_or_update_file(self, *, path: str, filename: str, extension: str, size_bytes: int, modified_at: str, file_hash: str, mime_type: str, metadata: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO files (path, filename, extension, size_bytes, modified_at, hash, mime_type, indexed_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename = excluded.filename,
                    extension = excluded.extension,
                    size_bytes = excluded.size_bytes,
                    modified_at = excluded.modified_at,
                    hash = excluded.hash,
                    mime_type = excluded.mime_type,
                    indexed_at = datetime('now'),
                    metadata_json = excluded.metadata_json
                """,
                (path, filename, extension, size_bytes, modified_at, file_hash, mime_type, json.dumps(metadata, ensure_ascii=False)),
            )
            conn.commit()

    def delete_file(self, path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
            if row is not None:
                conn.execute("DELETE FROM fts_chunks WHERE file_id = ?", (row[0],))
                conn.execute("DELETE FROM chunks WHERE file_id = ?", (row[0],))
            conn.execute("DELETE FROM files WHERE path = ?", (path,))
            conn.commit()

    def delete_file_chunks(self, file_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id FROM files WHERE path = ?", (file_path,)).fetchone()
            if row is None:
                return
            conn.execute("DELETE FROM fts_chunks WHERE file_id = ?", (row[0],))
            conn.execute("DELETE FROM chunks WHERE file_id = ?", (row[0],))
            conn.commit()

    def add_chunk(self, file_path: str, chunk_index: int, content: str, page_number: int | None = None, cell_number: int | None = None, metadata: dict[str, Any] | None = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id, filename FROM files WHERE path = ?", (file_path,)).fetchone()
            if row is None:
                raise ValueError(f"File not found in database: {file_path}")
            file_id, filename = row
            chunk_metadata = json.dumps(metadata or {}, ensure_ascii=False)
            cursor = conn.execute(
                """
                INSERT INTO chunks (file_id, chunk_index, content, page_number, cell_number, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (file_id, chunk_index, content, page_number, cell_number, chunk_metadata),
            )
            chunk_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO fts_chunks (rowid, content, file_id, file_path, filename)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chunk_id, content, file_id, file_path, filename),
            )
            conn.commit()

    def get_file_by_path(self, path: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, path, filename, extension, size_bytes, modified_at, hash, mime_type, indexed_at, metadata_json
                FROM files WHERE path = ?
                """,
                (path,),
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "path": row[1],
                "filename": row[2],
                "extension": row[3],
                "size_bytes": row[4],
                "modified_at": row[5],
                "hash": row[6],
                "mime_type": row[7],
                "indexed_at": row[8],
                "metadata": json.loads(row[9] or "{}"),
            }

    def list_files(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, path, filename, extension, size_bytes, modified_at, hash, mime_type, indexed_at, metadata_json
                FROM files ORDER BY path
                """
            ).fetchall()
            return [
                {
                    "id": row[0],
                    "path": row[1],
                    "filename": row[2],
                    "extension": row[3],
                    "size_bytes": row[4],
                    "modified_at": row[5],
                    "hash": row[6],
                    "mime_type": row[7],
                    "indexed_at": row[8],
                    "metadata": json.loads(row[9] or "{}"),
                }
                for row in rows
            ]

    def get_file_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM files").fetchone()[0])
