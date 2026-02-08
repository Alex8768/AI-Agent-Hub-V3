"""
Contracts for Vector RAG layer.
Based on ARCHITECTURE_V3 design.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SearchResult:
    """Result of vector search."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    explanation: Optional[str] = None


class AbstractEmbedder(ABC):
    """Contract for embedding models."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of texts."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding dimensions."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model name."""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Maximum tokens per text."""
        pass


class AbstractVectorStore(ABC):
    """Contract for vector stores."""
    
    @abstractmethod
    async def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add chunks to store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        filter_criteria: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, doc_id: str) -> int:
        """Delete all chunks of a document."""
        pass
    
    @abstractmethod
    async def update_chunk(self, chunk_id: str, updates: Dict[str, Any]) -> bool:
        """Update chunk metadata."""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all data."""
        pass


class AbstractRAGEngine(ABC):
    """Contract for RAG engines."""
    
    @abstractmethod
    async def add_document(
        self,
        document: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Add document to RAG system."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """Search with RAG."""
        pass
    
    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Retrieve context for LLM."""
        pass
    
    @abstractmethod
    async def get_document_stats(self, doc_id: str) -> Dict[str, Any]:
        """Get document statistics."""
        pass
