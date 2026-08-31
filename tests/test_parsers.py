from pathlib import Path

from localsearch.parsers import parse_file


def test_parse_python_file_extracts_symbols(tmp_path):
    path = tmp_path / "model.py"
    path.write_text(
        '''
import torch

# Train the model

def train_model():
    """Train a network."""
    return "done"

class Model:
    pass
'''.strip(),
        encoding="utf-8",
    )

    parsed = parse_file(path)

    assert parsed.extension == ".py"
    assert "train_model" in parsed.text
    assert "Model" in parsed.text
    assert "torch" in parsed.text
    assert "Train the model" in parsed.text


def test_parse_notebook_file_extracts_cell_boundaries(tmp_path):
    path = tmp_path / "breast.ipynb"
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Breast Model\n", "Dataset summary\n"]},
            {"cell_type": "code", "source": ["import pandas as pd\n", "X = pd.read_csv('x.csv')\n"]},
            {"cell_type": "code", "source": ["scaler = StandardScaler()\n", "model = 'pytorch'\n"]},
        ],
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(__import__("json").dumps(notebook), encoding="utf-8")

    parsed = parse_file(path)

    assert parsed.extension == ".ipynb"
    assert "Cell 1" in parsed.text
    assert "Breast Model" in parsed.text
    assert "Cell 2" in parsed.text
    assert "StandardScaler" in parsed.text


def test_parse_json_and_csv_files(tmp_path):
    json_path = tmp_path / "config.json"
    json_path.write_text('{"model": "pytorch", "layers": 3}', encoding="utf-8")

    json_parsed = parse_file(json_path)
    assert "pytorch" in json_parsed.text
    assert "layers" in json_parsed.text

    csv_path = tmp_path / "data.csv"
    csv_path.write_text("name,score\nalpha,10\n", encoding="utf-8")

    csv_parsed = parse_file(csv_path)
    assert "name" in csv_parsed.text
    assert "alpha" in csv_parsed.text


def test_parse_markdown_file_preserves_headings(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Neural Network\n\nThis is a summary of pruning.\n", encoding="utf-8")

    parsed = parse_file(path)

    assert parsed.extension == ".md"
    assert "Neural Network" in parsed.text
    assert "pruning" in parsed.text
