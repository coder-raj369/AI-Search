from __future__ import annotations

from pathlib import Path

from localsearch.parsers.base import ParsedDocument


def parse_file(path: str | Path) -> ParsedDocument:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        from localsearch.parsers.python import PythonParser

        return PythonParser().parse(file_path)
    if suffix == ".ipynb":
        from localsearch.parsers.notebook import NotebookParser

        return NotebookParser().parse(file_path)
    if suffix == ".md":
        from localsearch.parsers.markdown import MarkdownParser

        return MarkdownParser().parse(file_path)
    if suffix in {".txt", ".html", ".xml"}:
        from localsearch.parsers.text import TextParser

        return TextParser().parse(file_path)
    if suffix == ".json":
        from localsearch.parsers.json import JSONParser

        return JSONParser().parse(file_path)
    if suffix == ".csv":
        from localsearch.parsers.csv import CSVParser

        return CSVParser().parse(file_path)
    if suffix == ".pdf":
        from localsearch.parsers.pdf import PDFParser

        return PDFParser().parse(file_path)

    from localsearch.parsers.text import TextParser

    return TextParser().parse(file_path)
