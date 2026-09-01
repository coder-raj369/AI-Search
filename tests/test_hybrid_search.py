from localsearch.indexing.indexer import index_directory
from localsearch.retrieval.hybrid import hybrid_search


def test_hybrid_search_fuses_bm25_and_semantic_results(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    relevant = root / "debug_model.py"
    relevant.write_text(
        """
import torch
from sklearn.preprocessing import StandardScaler

# tensor mismatch debugging
X = StandardScaler().fit_transform(X)
""".strip(),
        encoding="utf-8",
    )

    other = root / "notes.txt"
    other.write_text("This note is about travel plans and daily journaling.\n", encoding="utf-8")

    db_path = tmp_path / "hybrid.db"
    index_directory([str(root)], db_path=str(db_path))

    results = hybrid_search("torch StandardScaler tensor mismatch", db_path=str(db_path), limit=5)

    assert results
    assert results[0]["path"] == str(relevant)


def test_hybrid_search_supports_file_type_filter(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    first = root / "model.py"
    first.write_text("torch.nn.Linear(10, 5)\n", encoding="utf-8")

    second = root / "summary.md"
    second.write_text("Description of a neural network.\n", encoding="utf-8")

    db_path = tmp_path / "hybrid.db"
    index_directory([str(root)], db_path=str(db_path))

    results = hybrid_search("neural network", db_path=str(db_path), limit=10, file_type=".py")

    assert results
    assert all(result["path"].endswith(".py") for result in results)
