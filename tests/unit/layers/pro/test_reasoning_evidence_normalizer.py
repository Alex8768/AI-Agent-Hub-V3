from __future__ import annotations

from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result


def test_normalize_retrieval_result_happy_path():
    result = {
        "results": [{"chunk_id": "chunk:1"}, {"chunk_id": "chunk:2"}],
        "graph": {"nodes": [{"id": "node:1"}], "edges": [{"id": "edge:1"}]},
        "evidence": [
            {"type": "chunk", "id": "chunk:1", "source_refs": ["doc:A#1"], "confidence": 0.9},
            {"bad": "shape"},
        ],
    }

    prov, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)

    assert used_chunks == ["chunk:1", "chunk:2"]
    assert used_nodes == ["node:1"]
    assert used_edges == ["edge:1"]

    assert len(prov) == 1
    assert prov[0].type == "chunk"
    assert prov[0].id == "chunk:1"
    assert prov[0].source_refs == ["doc:A#1"]
    assert prov[0].confidence == 0.9

    assert preview_items == ["doc:A#1"]


def test_normalize_retrieval_result_non_dict_is_empty():
    prov, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(None)
    assert prov == []
    assert used_chunks == []
    assert used_nodes == []
    assert used_edges == []
    assert preview_items == []
