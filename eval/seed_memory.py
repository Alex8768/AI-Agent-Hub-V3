from __future__ import annotations

import sys
from pathlib import Path as _Path

# Make 'src' importable when running as a script (outside pytest)
_ROOT = _Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / 'src'))

import asyncio
import os
from typing import Any


SEED_ITEMS: list[tuple[str, str, dict[str, Any]]] = [
    ("about.platform", "AI Agent Hub V3 is an enterprise AI agent platform with Base and Pro layers.", {"tags": ["about", "platform"]}),
    ("about.retrieval", "Retrieval sources: vector (FAISS/Qdrant), graph (GraphRAG), memory (semantic + fallback).", {"tags": ["retrieval"]}),
    ("about.reasoning", "Reasoning endpoint /api/v1/answer is feature-gated and returns evidence + diagnostics.", {"tags": ["reasoning"]}),
    ("about.di", "Composition root wires heavy dependencies in lifespan; endpoints stay thin.", {"tags": ["architecture", "di"]}),
    ("about.eval", "Eval harness uses trace_id and debug snapshot to detect quality regressions.", {"tags": ["eval"]}),
]


async def main() -> int:
    # Ensure Pro memory is enabled for seeding
    os.environ.setdefault("FEATURE_MEMORY", "true")
    # Optional: enable embeddings indexing if you want (requires qdrant running)
    # os.environ.setdefault("FEATURE_MEMORY_EMBEDDINGS", "true")

    from src.core.initializer import initialize_core_components, cleanup_core_components
    from src.core.providers import get_memory_store

    await initialize_core_components()
    try:
        store = get_memory_store()

        ws = os.environ.get("WORKSPACE_ID", "default")

        for key, value, meta in SEED_ITEMS:
            await store.put(workspace_id=ws, key=key, value=value, metadata=meta)

        print(f"OK: seeded {len(SEED_ITEMS)} memory items into workspace={ws}")
        return 0
    finally:
        await cleanup_core_components()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
