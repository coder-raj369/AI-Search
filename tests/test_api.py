from fastapi.testclient import TestClient

from localsearch.api.app import create_app
from localsearch.indexing.indexer import index_directory


def test_health_and_stats_endpoints(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "notes.txt").write_text("local search notes", encoding="utf-8")
    db_path = tmp_path / "api.db"
    index_directory([str(root)], db_path=str(db_path))

    client = TestClient(create_app(db_path=str(db_path)))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["files"] == 1
    assert stats.json()["chunks"] == 1


def test_search_endpoint_supports_lexical_mode(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    target = root / "model.py"
    target.write_text("torch tensor debugging", encoding="utf-8")
    db_path = tmp_path / "api.db"
    index_directory([str(root)], db_path=str(db_path))

    client = TestClient(create_app(db_path=str(db_path)))
    response = client.post(
        "/search",
        json={"query": "tensor debugging", "mode": "lexical", "limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "tensor debugging"
    assert payload["results"][0]["path"] == str(target)


def test_file_detail_validates_file_id(tmp_path):
    db_path = tmp_path / "api.db"
    client = TestClient(create_app(db_path=str(db_path)))

    response = client.get("/files/999")

    assert response.status_code == 404
