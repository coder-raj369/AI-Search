import json

from localsearch.cli import main


def test_cli_index_and_stats_use_real_database(tmp_path, capsys, monkeypatch):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "notes.txt").write_text("tensor debugging notes", encoding="utf-8")
    db_path = tmp_path / "search.db"

    monkeypatch.setattr("sys.argv", ["localsearch", "index", str(root), "--db", str(db_path)])
    assert main() == 0
    assert "New: 1" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["localsearch", "stats", "--db", str(db_path)])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Files: 1" in output
    assert "Chunks: 1" in output


def test_cli_search_returns_real_json_results(tmp_path, capsys, monkeypatch):
    root = tmp_path / "docs"
    root.mkdir()
    target = root / "notes.txt"
    target.write_text("tensor debugging notes", encoding="utf-8")
    db_path = tmp_path / "search.db"

    monkeypatch.setattr("sys.argv", ["localsearch", "index", str(root), "--db", str(db_path)])
    assert main() == 0
    capsys.readouterr()

    monkeypatch.setattr(
        "sys.argv",
        ["localsearch", "search", "tensor", "--mode", "lexical", "--db", str(db_path), "--json"],
    )
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["path"] == str(target)
    assert payload["mode"] == "lexical"
