from __future__ import annotations

from src.layers.pro.rag.retrieval.policy import RetrievalPolicy, apply_policy


def test_retrieval_policy_source_budgets_limit_each_type_after_rerank():
    evidence = []
    # make a lot of each type with same score so ordering is deterministic by type+id
    for i in range(10):
        evidence.append({"type": "chunk", "id": f"c{i}", "score": 1.0, "confidence": 0.5})
    for i in range(10):
        evidence.append({"type": "memory", "id": f"m{i}", "score": 1.0, "confidence": 0.5})
    for i in range(10):
        evidence.append({"type": "edge", "id": f"e{i}", "score": 1.0, "confidence": 0.5})

    policy = RetrievalPolicy(
        similarity_threshold=0.0,
        max_evidence=50,
        dedupe=True,
        rerank=True,
        max_chunks=3,
        max_memory=2,
        max_edges=4,
    )
    out, stats = apply_policy(evidence, policy=policy)

    types = [x.get("type") for x in out]
    assert types.count("chunk") == 3
    assert types.count("memory") == 2
    assert types.count("edge") == 4

    assert stats["budget_applied"] is True
    assert stats["budget_chunks_used"] == 3
    assert stats["budget_memory_used"] == 2
    assert stats["budget_edges_used"] == 4
