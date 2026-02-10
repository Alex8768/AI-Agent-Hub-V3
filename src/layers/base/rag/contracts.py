"""
Contracts for Vector RAG layer.
Based on ARCHITECTURE_V3 design.

Single source of truth for Embedder/VectorStore/SearchResult is src.core.contracts.
This module provides backward-compatible aliases + RAG-specific engine contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.core.contracts import EmbeddingModel, SearchResult, VectorStore

# Backward-compatible aliases (legacy names used across Base layer)
AbstractEmbedder = EmbeddingModel
AbstractVectorStore = VectorStore


class AbstractRAGEngine(ABC):
    """Contract for RAG engines."""

    @abstractmethod
    async def add_document(
        self,
        document: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """Add document to RAG system."""
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        **kwargs,
    ) -> List[SearchResult]:
        """Search with RAG."""
        raise NotImplementedError

    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        max_tokens: int = 4000,
        **kwargs,
    ) -> str:
        """Retrieve context for LLM."""
        raise NotImplementedError

    @abstractmethod
    async def get_document_stats(self, doc_id: str) -> Dict[str, Any]:
        """Get document statistics."""
        raise NotImplementedError


__all__ = [
    "EmbeddingModel",
    "VectorStore",
    "SearchResult",
    "AbstractEmbedder",
    "AbstractVectorStore",
    "AbstractRAGEngine",
]
