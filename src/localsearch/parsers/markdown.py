from __future__ import annotations

from pathlib import Path

from localsearch.parsers.base import ParsedDocument


class MarkdownParser:
    def parse(self, path: str | Path) -> ParsedDocument:
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return ParsedDocument(
            path=str(file_path),
            extension=file_path.suffix.lower(),
            text=text,
            metadata={"source": "markdown"},
            language="markdown",
        )
