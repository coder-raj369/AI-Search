from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


_DEFAULT_SUPPORTED_EXTENSIONS = {
    ".py",
    ".ipynb",
    ".md",
    ".txt",
    ".pdf",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".xml",
}

_DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    ".DS_Store",
    "dist",
    "build",
    "target",
}


@dataclass
class LocalSearchConfig:
    root_paths: list[str] = field(default_factory=lambda: [str(Path.home())])
    supported_extensions: set[str] = field(default_factory=lambda: set(_DEFAULT_SUPPORTED_EXTENSIONS))
    ignored_dirs: set[str] = field(default_factory=lambda: set(_DEFAULT_IGNORED_DIRS))
    max_file_size_bytes: int = 500 * 1024 * 1024
    follow_symlinks: bool = False
    enable_hidden_files: bool = False

    @classmethod
    def from_mapping(cls, mapping: dict | None = None) -> "LocalSearchConfig":
        mapping = mapping or {}
        data = {**mapping}
        supported = data.get("supported_extensions") or _DEFAULT_SUPPORTED_EXTENSIONS
        ignored = data.get("ignored_dirs") or _DEFAULT_IGNORED_DIRS
        return cls(
            root_paths=list(data.get("root_paths", [str(Path.home())])),
            supported_extensions=set(supported),
            ignored_dirs=set(ignored),
            max_file_size_bytes=int(data.get("max_file_size_bytes", 500 * 1024 * 1024)),
            follow_symlinks=bool(data.get("follow_symlinks", False)),
            enable_hidden_files=bool(data.get("enable_hidden_files", False)),
        )

    def should_include_file(self, path: Path) -> bool:
        if path.is_symlink() and not self.follow_symlinks:
            return False
        if path.name.startswith(".") and not self.enable_hidden_files:
            return False
        if path.suffix.lower() not in self.supported_extensions:
            return False
        return True

    def should_skip_dir(self, dir_name: str) -> bool:
        return dir_name in self.ignored_dirs

    def normalize_root(self) -> list[Path]:
        return [Path(p).expanduser().resolve() for p in self.root_paths]
