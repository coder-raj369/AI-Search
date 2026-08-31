from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from localsearch.config import LocalSearchConfig


@dataclass(frozen=True)
class FileRecord:
    path: str
    filename: str
    extension: str
    size_bytes: int
    is_symlink: bool = False


def scan_paths(paths: Iterable[str], config: LocalSearchConfig | None = None) -> list[FileRecord]:
    config = config or LocalSearchConfig()
    discovered: list[FileRecord] = []
    seen: set[str] = set()

    for raw_path in paths:
        root = Path(raw_path).expanduser().resolve()
        if not root.exists():
            continue

        for file_path in iter_files(root, config):
            normalized_path = str(file_path.resolve())
            if normalized_path in seen:
                continue
            seen.add(normalized_path)
            discovered.append(
                FileRecord(
                    path=str(file_path),
                    filename=file_path.name,
                    extension=file_path.suffix.lower(),
                    size_bytes=file_path.stat().st_size,
                    is_symlink=file_path.is_symlink(),
                )
            )

    return discovered


def iter_files(root: Path, config: LocalSearchConfig) -> Iterable[Path]:
    if not root.exists():
        return []

    queue = [root]
    visited_dirs: set[Path] = set()

    while queue:
        current = queue.pop()
        if current in visited_dirs:
            continue
        visited_dirs.add(current)

        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name.lower())
        except (PermissionError, OSError):
            continue

        for entry in entries:
            if entry.is_symlink() and not config.follow_symlinks:
                continue
            if entry.name.startswith(".") and not config.enable_hidden_files and entry.is_dir():
                continue
            if entry.is_dir():
                if config.should_skip_dir(entry.name):
                    continue
                queue.append(entry)
                continue
            if not entry.is_file():
                continue
            if not config.should_include_file(entry):
                continue
            if entry.stat().st_size > config.max_file_size_bytes:
                continue
            yield entry
