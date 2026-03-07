from __future__ import annotations

import pytest

from src.layers.pro.reasoning.graph.nodes import search_node
from src.layers.pro.reasoning.graph.state import AgentState


class _RetrieverRequestOnly:
    async def retrieve(self, request):
        assert getattr(request, "query", "") == "Q?"
        return {
            "results": [{"chunk_id": "c1"}],
            "graph": {"nodes": [{"id": "n1"}], "edges": [{"id": "e1"}]},
            "evidence": [
                {"type": "chunk", "id": "c1", "source_refs": ["doc:R#1"], "confidence": 0.8},
            ],
        }


@pytest.mark.asyncio
async def test_search_node_supports_request_object_retriever_signature():
    state = AgentState(query="Q?", workspace_id="default")
    out = await search_node(state, _RetrieverRequestOnly())

    assert out.error is None
    assert out.used_chunks == ["c1"]
    assert out.used_nodes == ["n1"]
    assert out.used_edges == ["e1"]
    assert out.context_preview == "doc:R#1"
    assert len(out.provenance) == 1
