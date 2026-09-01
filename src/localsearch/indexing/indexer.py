from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from localsearch.config import LocalSearchConfig
from localsearch.database.connection import DatabaseManager
from localsearch.indexing.hashing import compute_file_hash
from localsearch.parsers import parse_file
from localsearch.scanner.discovery import FileRecord, scan_paths


def _normalize_metadata(path: str, file_hash: str, size_bytes: int, modified_at: str, parsed: Any) -> dict[str, Any]:
    metadata = {
        "path": path,
        "hash": file_hash,
        "size_bytes": size_bytes,
        "modified_at": modified_at,
        "language": getattr(parsed, "language", None),
        "extension": parsed.extension,
    }
    metadata.update(getattr(parsed, "metadata", {}) or {})
    return metadata


def _chunk_text(text: str, chunk_size: int = 1200) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    for start in range(0, len(text), chunk_size):
        chunk = text[start : start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def index_directory(paths: list[str], db_path: str | Path = "localsearch.db", config: LocalSearchConfig | None = None) -> dict[str, int]:
    config = config or LocalSearchConfig()
    db = DatabaseManager(db_path)
    scanned = scan_paths(paths, config=config)
    current_paths = {record.path for record in scanned}

    existing = {record["path"]: record for record in db.list_files()}
    deleted = sorted(set(existing) - current_paths)
    for path in deleted:
        db.delete_file(path)

    summary = {
        "new": 0,
        "updated": 0,
        "deleted": 0,
        "unchanged": 0,
        "indexed_files": 0,
    }

    for record in scanned:
        file_path = Path(record.path)
        file_hash = compute_file_hash(file_path)
        stat = file_path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        existing_record = existing.get(record.path)
        if existing_record and existing_record.get("hash") == file_hash and existing_record.get("size_bytes") == record.size_bytes:
            summary["unchanged"] += 1
            continue

        parsed = parse_file(file_path)
        metadata = _normalize_metadata(record.path, file_hash, record.size_bytes, modified_at, parsed)
        db.insert_or_update_file(
            path=record.path,
            filename=record.filename,
            extension=record.extension,
            size_bytes=record.size_bytes,
            modified_at=modified_at,
            file_hash=file_hash,
            mime_type="application/octet-stream",
            metadata=metadata,
        )

        db.delete_file_chunks(record.path)

        chunks = _chunk_text(parsed.text)
        for index, chunk in enumerate(chunks):
            db.add_chunk(
                record.path,
                chunk_index=index,
                content=chunk,
                page_number=None,
                cell_number=None,
                metadata={"source": parsed.metadata.get("source", "text")},
            )

        if existing_record is None:
            summary["new"] += 1
        else:
            summary["updated"] += 1

        summary["indexed_files"] += 1

    summary["deleted"] = len(deleted)
    return summary
