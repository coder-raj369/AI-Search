from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    path: str
    extension: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str | None = None
