from localsearch.retrieval.reranker import rerank_results


def test_reranker_adds_grounded_explanation_and_preserves_best_match():
    candidates = [
        {
            "path": "/tmp/notes.txt",
            "filename": "notes.txt",
            "extension": ".txt",
            "score": 0.02,
            "snippet": "A general model note.",
            "metadata": {},
        },
        {
            "path": "/tmp/debug_model.py",
            "filename": "debug_model.py",
            "extension": ".py",
            "score": 0.02,
            "snippet": "RuntimeError: mat1 and mat2 shapes cannot be multiplied",
            "metadata": {"language": "python"},
        },
    ]

    results = rerank_results("tensor shape error", candidates)

    assert results[0]["filename"] == "debug_model.py"
    assert results[0]["why_matched"]
    assert any("tensor" in evidence.lower() or "shape" in evidence.lower() for evidence in results[0]["why_matched"])
    assert results[0]["rerank_score"] > results[1]["rerank_score"]


def test_reranker_returns_empty_for_empty_candidates():
    assert rerank_results("anything", []) == []
