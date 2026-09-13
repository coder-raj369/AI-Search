from __future__ import annotations

import ast
from pathlib import Path

from localsearch.parsers.base import ParsedDocument


class PythonParser:
    def parse(self, path: str | Path) -> ParsedDocument:
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8", errors="replace")

        functions: list[str] = []
        classes: list[str] = []
        imports: list[str] = []
        parse_error: str | None = None

        try:
            module = ast.parse(text)
        except SyntaxError as exc:
            parse_error = f"SyntaxError: {exc.msg} (line {exc.lineno})"
        else:
            for node in ast.walk(module):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.get_source_segment(text, node) or "")

        content_parts = [text]
        if functions:
            content_parts.append("functions: " + ", ".join(functions))
        if classes:
            content_parts.append("classes: " + ", ".join(classes))
        if imports:
            content_parts.append("imports: " + "; ".join(imports))

        content = "\n".join(part.strip() for part in content_parts if part and part.strip())
        return ParsedDocument(
            path=str(file_path),
            extension=file_path.suffix.lower(),
            text=content,
            metadata={
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "source": "python",
                "parse_error": parse_error,
            },
            language="python",
        )
