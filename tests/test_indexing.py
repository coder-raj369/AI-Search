from pathlib import Path

from localsearch.database.connection import DatabaseManager
from localsearch.indexing.indexer import index_directory


def test_index_directory_tracks_new_updated_deleted_and_unchanged(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()

    old_file = root / "alpha.py"
    old_file.write_text("print('old')\n", encoding="utf-8")
    second_file = root / "beta.txt"
    second_file.write_text("hello world\n", encoding="utf-8")
    unchanged_file = root / "gamma.md"
    unchanged_file.write_text("keep me stable\n", encoding="utf-8")

    db_path = tmp_path / "index.db"
    summary = index_directory([str(root)], db_path=str(db_path))

    assert summary["new"] == 3
    assert summary["updated"] == 0
    assert summary["deleted"] == 0
    assert summary["unchanged"] == 0

    old_file.write_text("print('updated')\n", encoding="utf-8")
    extra_file = root / "delta.py"
    extra_file.write_text("print('new')\n", encoding="utf-8")
    removed_file = root / "beta.txt"
    removed_file.unlink()

    summary = index_directory([str(root)], db_path=str(db_path))

    assert summary["new"] == 1
    assert summary["updated"] == 1
    assert summary["deleted"] == 1
    assert summary["unchanged"] == 1

    manager = DatabaseManager(str(db_path))
    assert manager.get_file_count() == 3
    rows = manager.list_files()
    assert {row["path"] for row in rows} == {
        str(old_file),
        str(unchanged_file),
        str(extra_file),
    }


def test_hashing_and_metadata_are_persisted(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    file_path = root / "model.py"
    file_path.write_text("def train_model():\n    return True\n", encoding="utf-8")

    db_path = tmp_path / "index.db"
    summary = index_directory([str(root)], db_path=str(db_path))

    assert summary["indexed_files"] == 1
    manager = DatabaseManager(str(db_path))
    record = manager.get_file_by_path(str(file_path))

    assert record is not None
    assert record["filename"] == "model.py"
    assert record["extension"] == ".py"
    assert record["hash"]
    assert record["size_bytes"] > 0
