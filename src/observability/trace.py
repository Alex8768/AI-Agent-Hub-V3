from __future__ import annotations

import hashlib


def make_trace_id(*, workspace_id: str, query: str, k: int, graph_depth: int) -> str:
    """Deterministic trace id for evaluation and comparisons.

    Uses a stable hash of key request fields. Does NOT include request_id.
    """
    w = workspace_id or ""
    q = query or ""
    payload = f"w={w}\nq={q}\nk={int(k)}\nd={int(graph_depth)}".encode("utf-8", errors="ignore")
    return hashlib.sha1(payload).hexdigest()
