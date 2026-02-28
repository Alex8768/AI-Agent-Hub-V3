from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import uuid
from dataclasses import dataclass


@dataclass
class _DummyState:
    request_id: str


@dataclass
class _DummyAppState:
    rag_engine: object | None = None
    hybrid_retriever: object | None = None


@dataclass
class _DummyApp:
    state: _DummyAppState


@dataclass
class _DummyHTTP:
    app: _DummyApp
    state: _DummyState
    headers: dict


async def _init_core():
    from src.core.initializer import initialize_core_components
    await initialize_core_components()


async def _cleanup_core():
    from src.core.initializer import cleanup_core_components
    await cleanup_core_components()


async def _warm_singletons(app_state: _DummyAppState):
    # RAGEngine singleton
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.core.providers import get_vector_store

        app_state.rag_engine = RAGEngine()
        await get_vector_store()
        print("✅ RAGEngine ready (vector store warmed)")
    except Exception as e:
        print("⚠️ RAGEngine warmup skipped:", e)

    # HybridRetriever singleton (Pro)
    try:
        from src.core.config import get_settings
        s = get_settings()
        if getattr(s, "feature_reasoning", False) and getattr(s, "feature_graphrag", False):
            from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever
            app_state.hybrid_retriever = HybridRetriever()
            print("✅ HybridRetriever ready (Pro)")
        else:
            print("ℹ️ HybridRetriever: SKIP (feature_reasoning/feature_graphrag disabled)")
    except Exception as e:
        print("⚠️ HybridRetriever warmup skipped:", e)


async def _ingest_demo_text(workspace_id: str) -> str | None:
    """Ingest small demo text via DocumentService (same path as API)."""
    text = "AI Agent Hub V3 golden path demo. This is a small document about retrieval and reasoning."
    try:
        from src.infrastructure.database import get_db
        from src.services.document.document_service import DocumentService

        svc = DocumentService()
        data = text.encode("utf-8")

        async with get_db() as db:
            rec = await svc.create_from_upload(
                db,
                filename="golden_path_demo.txt",
                data=data,
                workspace_id=workspace_id,
                mime="text/plain",
                chunk_size=800,
                chunk_overlap=120,
            )

        doc_id = getattr(rec, "id", None)
        print("✅ Ingest ok", {"doc_id": doc_id, "chunks": getattr(rec, "chunks_count", None), "status": getattr(rec, "status", None)})
        return str(doc_id) if doc_id else None
    except Exception as e:
        print("❌ Ingest failed:", e)
        return None


async def _search_demo(app_state: _DummyAppState, workspace_id: str):
    query = "What is this demo about?"
    engine = app_state.rag_engine
    if engine is None:
        print("⚠️ Search: SKIP (rag_engine missing)")
        return None

    # Try a few possible method names without assuming exact API
    candidates = ["search", "query", "retrieve", "answer"]
    for name in candidates:
        fn = getattr(engine, name, None)
        if callable(fn):
            try:
                res = await fn(query=query, k=5, workspace_id=workspace_id)  # type: ignore
                print(f"✅ Search via RAGEngine.{name}() ok")
                return res
            except TypeError:
                # Try without workspace_id if signature differs
                try:
                    res = await fn(query=query, k=5)  # type: ignore
                    print(f"✅ Search via RAGEngine.{name}() ok (no workspace_id)")
                    return res
                except Exception:
                    pass
            except Exception:
                pass

    print("ℹ️ Search: could not find compatible RAGEngine method (skipped)")
    return None


async def _answer_demo(app_state: _DummyAppState, workspace_id: str):
    try:
        from src.core.config import get_settings
        s = get_settings()
        if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
            print("ℹ️ Answer: SKIP (feature_reasoning/feature_graphrag disabled)")
            return None
    except Exception as e:
        print("⚠️ Answer: settings check failed:", e)
        return None

    if app_state.rag_engine is None or app_state.hybrid_retriever is None:
        print("⚠️ Answer: SKIP (rag_engine/hybrid_retriever missing)")
        return None

    try:
        from src.layers.pro.reasoning.contracts import AnswerRequest
        from src.services.answer.answer_service import AnswerService

        rid = str(uuid.uuid4())
        http = _DummyHTTP(
            app=_DummyApp(state=app_state),
            state=_DummyState(request_id=rid),
            headers={},
        )
        req = AnswerRequest(query="Summarize the demo content.", k=8, graph_depth=1, filters={})
        resp = await AnswerService().handle(http, req, workspace_id=workspace_id)

        diag = dict(getattr(resp, "diagnostics", {}) or {})
        print("✅ Answer ok")
        print("   trace_id:", diag.get("trace_id"))
        print("   top_evidence:", (diag.get("top_evidence") or [])[:5])
        print("   timings:", getattr(resp, "timings", None))
        return resp
    except Exception as e:
        print("❌ Answer failed:", e)
        return None


async def main():
    workspace_id = "default"
    app_state = _DummyAppState()

    await _init_core()
    try:
        await _warm_singletons(app_state)
        await _ingest_demo_text(workspace_id)
        await _search_demo(app_state, workspace_id)
        await _answer_demo(app_state, workspace_id)
    finally:
        await _cleanup_core()


if __name__ == "__main__":
    asyncio.run(main())
