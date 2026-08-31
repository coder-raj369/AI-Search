from __future__ import annotations

import json
from pathlib import Path

from localsearch.parsers.base import ParsedDocument


class JSONParser:
    def parse(self, path: str | Path) -> ParsedDocument:
        file_path = Path(path)
        payload = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return ParsedDocument(
            path=str(file_path),
            extension=file_path.suffix.lower(),
            text=text,
            metadata={"source": "json"},
            language="json",
        )
