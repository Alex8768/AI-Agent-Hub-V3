"""
Health endpoints.
Diagnostic, fast, non-fatal.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from fastapi import APIRouter

from src.core.config import settings
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
        meta_file = index_file.with_suffix(".meta.pkl")

        services["vector_store"] = {
            "status": "healthy" if index_file.exists() else "uninitialized",
            "provider": "faiss",
            "index_path": str(index_file),
            "index_exists": index_file.exists(),
            "meta_exists": meta_file.exists(),
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
        providers = await factory.get_available_providers()

        effective_device = getattr(settings, "embedding_device", None) or (
            "mps" if _is_mps_available() else "cpu"
        )

        services["embeddings"] = {
            "status": "healthy",
            "providers": providers,
            "cached_models": cached,
            "default_model": getattr(settings, "embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"),
            "effective_device": effective_device,
        }
    except Exception as e:
        services["embeddings"] = {"status": "unhealthy", "error": str(e)}

    # --- Export storage ---
    try:
        exports_dir = Path("./data/exports")
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
