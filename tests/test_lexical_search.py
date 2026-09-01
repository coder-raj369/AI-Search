from localsearch.indexing.indexer import index_directory
from localsearch.retrieval.bm25 import lexical_search


def test_lexical_search_ranks_relevant_file_first(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    model_file = root / "breast_model.py"
    model_file.write_text(
        """
import torch
from sklearn.preprocessing import StandardScaler

X = StandardScaler().fit_transform(X)
model = torch.nn.Linear(30, 1)
""".strip(),
        encoding="utf-8",
    )

    notes_file = root / "notes.txt"
    notes_file.write_text("This file contains model notes and torch references, but not the StandardScaler pipeline.\n", encoding="utf-8")

    db_path = tmp_path / "search.db"
    index_directory([str(root)], db_path=str(db_path))

    results = lexical_search("torch StandardScaler model", db_path=str(db_path), limit=5)

    assert results
    assert results[0]["path"] == str(model_file)
    assert results[0]["score"] > results[1]["score"]


def test_lexical_search_supports_type_and_path_filters(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    py_file = root / "first.py"
    py_file.write_text("print('pytorch error')\n", encoding="utf-8")

    text_file = root / "other.txt"
    text_file.write_text("pytorch error\n", encoding="utf-8")

    db_path = tmp_path / "search.db"
    index_directory([str(root)], db_path=str(db_path))

    results = lexical_search("pytorch error", db_path=str(db_path), limit=10, file_type=".py")

    assert results
    assert all(result["path"].endswith(".py") for result in results)
