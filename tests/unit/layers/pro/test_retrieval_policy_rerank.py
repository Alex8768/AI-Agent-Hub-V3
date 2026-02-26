from __future__ import annotations

from src.layers.pro.rag.retrieval.policy import RetrievalPolicy, apply_policy


def test_retrieval_policy_deterministic_rerank_orders_by_score_confidence_type_id():
    evidence = [
        {"type": "edge", "id": "e2", "score": 0.9, "confidence": 0.4},
        {"type": "chunk", "id": "c2", "score": 0.9, "confidence": 0.4},
        {"type": "chunk", "id": "c1", "score": 0.9, "confidence": 0.4},
        {"type": "chunk", "id": "c3", "score": 0.7, "confidence": 0.9},
        {"type": "edge", "id": "e1", "score": 0.9, "confidence": 0.6},
        {"type": "chunk", "id": "c4"},  # missing score/conf -> should go last among chunks
    ]

    policy = RetrievalPolicy(similarity_threshold=0.0, max_evidence=50, dedupe=True, rerank=True)
    out, stats = apply_policy(evidence, policy=policy)

    # Expectations:
    # - highest score first
    # - tie: higher confidence first
    # - tie: chunk before edge
    # - tie: id asc
    ids = [(x.get("type"), x.get("id")) for x in out]

    assert ids[0] == ("edge", "e1")  # score 0.9 conf 0.6 beats others
    # next: score 0.9 conf 0.4 chunks ordered by id asc, then edge e2
    assert ("chunk", "c1") in ids[1:4]
    assert ("chunk", "c2") in ids[1:4]
    assert ("edge", "e2") in ids[1:5]

    # lower score item after higher score group
    assert ids.index(("chunk", "c3")) > ids.index(("chunk", "c1"))
    # missing score/conf goes to the end
    assert ids[-1] == ("chunk", "c4")

    assert stats["rerank_applied"] is True
    assert stats["rerank_strategy"] == "score_confidence_type_id"
