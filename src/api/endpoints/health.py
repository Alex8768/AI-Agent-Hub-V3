# IO_GUARD: allow
"""
Health endpoints.
Diagnostic, fast, non-fatal.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from fastapi import APIRouter

from src.core.config import settings
from src.core.accelerator import accelerator
from src.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    now = datetime.datetime.utcnow().isoformat() + "Z"

    services = {
        "api": {"status": "healthy", "version": settings.app_version, "environment": settings.environment},
    }

    # --- Database ---
    try:
        from src.infrastructure.database import get_db
        from sqlalchemy import text

        async with get_db() as db:
            await db.execute(text("SELECT 1"))

            # Check documents table existence (SQLite)
            r = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"))
            has_documents = r.first() is not None

        services["database"] = {"status": "healthy", "documents_table": bool(has_documents)}
    except Exception as e:
        services["database"] = {"status": "unhealthy", "error": str(e)}

    # --- Vector store (FAISS) ---
    try:
        cfg = settings.get_vector_store_config()
        index_path = getattr(cfg, "path", None) or settings.faiss_index_path
        dimension = getattr(cfg, "dimension", None) or settings.faiss_dimension

        index_file = Path(index_path)
        meta_json_file = index_file.with_suffix(".meta.json")
        meta_pickle_file = index_file.with_suffix(".meta.pkl")
        meta_format = "json" if meta_json_file.exists() else ("pickle" if meta_pickle_file.exists() else "none")

        services["vector_store"] = {
            "status": "healthy" if index_file.exists() else "uninitialized",
            "provider": "faiss",
            "index_path": str(index_file),
            "index_exists": index_file.exists(),
            "meta_exists": bool(meta_json_file.exists() or meta_pickle_file.exists()),
            "meta_format": meta_format,
            "meta_json_exists": meta_json_file.exists(),
            "meta_pickle_exists": meta_pickle_file.exists(),
            "dimension": int(dimension),
        }
    except Exception as e:
        services["vector_store"] = {"status": "unhealthy", "error": str(e)}

    # --- Embeddings ---
    try:
        from src.adapters.embedding import get_embedding_factory
        from src.adapters.embedding.embedding_factory import _is_mps_available

        factory = get_embedding_factory()
        cached = factory.get_cached_models()
        cached_legacy = getattr(factory, 'get_cached_models_legacy', None)
        cached_legacy = cached_legacy() if callable(cached_legacy) else None
        providers = await factory.get_available_providers()

        requested = getattr(settings, "device", "auto") or "auto"
        effective_device = requested if requested != "auto" else accelerator.device

        services["embeddings"] = {
            "status": "healthy",
            "providers": providers,
            "cached_models": cached,
            "cached_models_legacy": cached_legacy or {},
            "default_model": getattr(settings, "embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"),
            "effective_device": effective_device,
            "hf_home": str(getattr(settings, "hf_home", None) or ""),
            "offline_mode": bool(getattr(settings, "hf_hub_offline", False) or getattr(settings, "transformers_offline", False)),
            "telemetry_disabled": bool(getattr(settings, "hf_hub_disable_telemetry", False)),
        }
    except Exception as e:
        services["embeddings"] = {"status": "unhealthy", "error": str(e)}

    # --- Export storage ---
    try:
        exports_dir = Path(settings.data_dir) / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        probe = exports_dir / ".health_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        services["export_storage"] = {"status": "healthy", "path": str(exports_dir)}
    except Exception as e:
        services["export_storage"] = {"status": "unhealthy", "error": str(e)}

    # --- Streaming publisher availability ---
    try:
        from src.core.config import settings as _s
        publisher_available = True
        try:
            import importlib
            importlib.import_module("src.layers.base.streaming.publishers.sse_publisher")
        except Exception:
            publisher_available = False

        services["streaming"] = {
            "status": "healthy" if _s.streaming_enabled else "disabled",
            "publisher_available": publisher_available,
        }
    except Exception as e:
        services["streaming"] = {"status": "unhealthy", "error": str(e)}

    overall = "healthy"
    # If any subsystem explicitly unhealthy => overall unhealthy
    for v in services.values():
        if isinstance(v, dict) and v.get("status") == "unhealthy":
            overall = "unhealthy"
            break

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=now,
        services=services,
    )


@router.get("/api/v1/health", include_in_schema=False)
async def api_health_check():
    return await health_check()


@router.get("/api/v1/health/deep", tags=["Health"])
async def health_deep():
    """
    Deep health check (manual):
    - DB query + documents table
    - Embeddings warm check (embed small text)
    - FAISS stats (loads index)
    Returns timings for each stage.
    """
    import time
    from sqlalchemy import text

    started = time.perf_counter()
    timings = {}
    details = {}

    # --- DB deep ---
    t0 = time.perf_counter()
    try:
        from src.infrastructure.database import get_db
        async with get_db() as db:
            await db.execute(text("SELECT 1"))
            r = await db.execute(text("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='documents'"))
            details["documents_table_exists"] = bool(r.scalar() or 0)
    except Exception as e:
        details["db_error"] = str(e)
    timings["db_seconds"] = round(time.perf_counter() - t0, 6)

    # --- Embeddings deep ---
    t0 = time.perf_counter()
    try:
        from src.adapters.embedding import get_embedding_factory
        factory = get_embedding_factory()
        model = await factory.create_embedding_model("sentence_transformer")
        vecs = await model.embed_documents(["deep health ping"])
        details["embedding_dim"] = len(vecs[0]) if vecs else None
        details["embeddings_cached_models"] = factory.get_cached_models()
        legacy_fn = getattr(factory, "get_cached_models_legacy", None)
        details["embeddings_cached_models_legacy"] = legacy_fn() if callable(legacy_fn) else {}
    except Exception as e:
        details["embeddings_error"] = str(e)
    timings["embeddings_seconds"] = round(time.perf_counter() - t0, 6)

    # --- Vector store deep ---
    t0 = time.perf_counter()
    try:
        from src.core.providers import get_vector_store
        from src.core.config import settings

        cfg = settings.get_vector_store_config()
        index_path = getattr(cfg, "path", None) or settings.faiss_index_path
        dimension = getattr(cfg, "dimension", None) or settings.faiss_dimension

        store = await get_vector_store()
        raw_stats = await store.get_stats()
        # Normalize to stable fields for observability
        details["vector_store_stats"] = {
            "provider": "faiss",
            "index_path": str(index_path),
            "dimension": int(dimension),
            "total_vectors": raw_stats.get("total_vectors") if isinstance(raw_stats, dict) else None,
            "raw": raw_stats,
        }
    except Exception as e:
        details["vector_store_error"] = str(e)
    timings["vector_store_seconds"] = round(time.perf_counter() - t0, 6)

    timings["total_seconds"] = round(time.perf_counter() - started, 6)

    overall = "healthy"
    if any(k.endswith("_error") for k in details.keys()):
        overall = "unhealthy"

    return {
        "status": overall,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "timings": timings,
        "details": details,
    }
