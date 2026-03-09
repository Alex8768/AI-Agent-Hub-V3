from __future__ import annotations

from types import SimpleNamespace

from src.api.endpoints.search_mapping import to_api_search_results, to_hybrid_search_response


def test_to_api_search_results_supports_model_dict_and_object_rows() -> None:
    rows = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "score": 0.9,
            "snippet": "a",
            "content": None,
            "source_document": "x.txt",
            "metadata": {},
        },
        SimpleNamespace(
            chunk_id="c2",
            document_id="d2",
            score=0.8,
            snippet="b",
            content=None,
            source_document="y.txt",
            metadata={},
        ),
    ]

    out = to_api_search_results(rows)
    assert [row.chunk_id for row in out] == ["c1", "c2"]


def test_to_hybrid_search_response_is_fail_safe_for_unexpected_shapes() -> None:
    out = to_hybrid_search_response(
        {"results": [], "graph": "bad", "evidence": {"bad": True}, "stats": "bad"}
    )
    assert out.results == []
    assert out.graph == {}
    assert out.evidence == []
    assert out.stats == {}
