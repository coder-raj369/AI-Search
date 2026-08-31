from __future__ import annotations

from pathlib import Path

from localsearch.parsers.base import ParsedDocument


class PDFParser:
    def parse(self, path: str | Path) -> ParsedDocument:
        file_path = Path(path)
        text = "[PDF text extraction unavailable in this minimal parser]"
        return ParsedDocument(
            path=str(file_path),
            extension=file_path.suffix.lower(),
            text=text,
            metadata={"source": "pdf", "status": "placeholder"},
            language="pdf",
        )
