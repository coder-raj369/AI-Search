from __future__ import annotations

import json
from pathlib import Path

from localsearch.parsers.base import ParsedDocument


class NotebookParser:
    def parse(self, path: str | Path) -> ParsedDocument:
        file_path = Path(path)
        payload = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))

        cells: list[str] = []
        for index, cell in enumerate(payload.get("cells", []), start=1):
            cell_type = cell.get("cell_type", "code")
            source = cell.get("source", [])
            if isinstance(source, str):
                source_text = source
            else:
                source_text = "".join(source)

            if not source_text.strip():
                continue

            cells.append(f"Cell {index} [{cell_type}]\n{source_text.strip()}")

        text = "\n\n".join(cells)
        return ParsedDocument(
            path=str(file_path),
            extension=file_path.suffix.lower(),
            text=text,
            metadata={
                "cell_count": len(cells),
                "source": "notebook",
                "notebook_metadata": payload.get("metadata", {}),
            },
            language="notebook",
        )
