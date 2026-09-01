import json

from localsearch.indexing.indexer import index_directory
from localsearch.retrieval.semantic import semantic_search


def test_semantic_search_prefers_relevant_notebook(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    relevant = root / "debug_notebook.ipynb"
    relevant.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["# Debugging\n"]},
                    {
                        "cell_type": "code",
                        "source": [
                            "RuntimeError: mat1 and mat2 shapes cannot be multiplied\n",
                            "X = torch.randn(32, 128)\n",
                            "W = torch.randn(128, 64)\n",
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    unrelated = root / "notes.md"
    unrelated.write_text("This note describes a recipe for lasagna and a weekend trip.\n", encoding="utf-8")

    db_path = tmp_path / "semantic.db"
    index_directory([str(root)], db_path=str(db_path))

    results = semantic_search("tensor dimension mismatch problem", db_path=str(db_path), limit=5)

    assert results
    assert results[0]["path"] == str(relevant)


def test_semantic_search_supports_type_filters(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    py_file = root / "network.py"
    py_file.write_text("torch.nn.Linear(3, 5)\n", encoding="utf-8")

    md_file = root / "summary.md"
    md_file.write_text("This file is about cooking and hiking.\n", encoding="utf-8")

    db_path = tmp_path / "semantic.db"
    index_directory([str(root)], db_path=str(db_path))

    results = semantic_search("neural network model", db_path=str(db_path), limit=10, file_type=".py")

    assert results
    assert all(result["path"].endswith(".py") for result in results)
