# 📄 ФАЙЛ: src/services/document/__init__.py
"""
Document services for AI Agent Hub V3.
ARCHITECTURE_V3: Services Layer - Document Management
"""

from .ingest_service import (
    IngestService,
    ChunkingStrategy,
    DocumentFormat,
    IngestResult,
    Chunk,
)

__all__ = [
    "IngestService",
    "ChunkingStrategy",
    "DocumentFormat", 
    "IngestResult",
    "Chunk",
]