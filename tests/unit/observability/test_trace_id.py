from __future__ import annotations

from src.observability.trace import make_trace_id


def test_make_trace_id_is_deterministic():
    a = make_trace_id(workspace_id="w1", query="hello", k=8, graph_depth=1)
    b = make_trace_id(workspace_id="w1", query="hello", k=8, graph_depth=1)
    assert a == b
    assert len(a) == 40  # sha1 hex length


def test_make_trace_id_changes_on_inputs():
    base = make_trace_id(workspace_id="w1", query="hello", k=8, graph_depth=1)
    assert base != make_trace_id(workspace_id="w2", query="hello", k=8, graph_depth=1)
    assert base != make_trace_id(workspace_id="w1", query="hello!", k=8, graph_depth=1)
    assert base != make_trace_id(workspace_id="w1", query="hello", k=9, graph_depth=1)
    assert base != make_trace_id(workspace_id="w1", query="hello", k=8, graph_depth=2)
