from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable
# ============ EMBEDDING CONTRACTS = ============
class EmbeddingModel(Configurable, HealthCheckable, ABC):
    """
    Contract for embedding models with asymmetric search support.
    Optimized for advanced RAG systems with query/document separation.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the embedding model."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimension of embeddings (vector size)."""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Maximum tokens per input text."""
        pass
    
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query/sentence.
        May add query-specific prefixes for asymmetric search models.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        pass
    
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents/sentences with batch optimization.
        Optimized for GPU/NPU parallel processing.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass


class EmbeddingFactory(ABC):
    """Factory for creating embedding models."""
    
    @abstractmethod
    async def create_embedding_model(
        self,
        provider_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> EmbeddingModel:
        """
        Create an embedding model from configuration.
        
        Args:
            provider_type: Type of embedding provider
            config: Configuration dictionary
            
        Returns:
            EmbeddingModel instance
        """
        pass
    
    @abstractmethod
    async def get_available_providers(self) -> List[str]:
        """Get list of available provider types."""
        pass
