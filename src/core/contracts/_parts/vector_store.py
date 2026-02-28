from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable
# ============ VECTOR STORE CONTRACTS = ============
@dataclass
class VectorDocument:
    """Document for vector storage."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Result of vector search."""
    document: VectorDocument
    score: float
    distance: float


class VectorStore(Configurable, Initializable, HealthCheckable, ABC):
    """Contract for vector stores."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the vector store."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensionality of embeddings."""
        pass
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[VectorDocument],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings
            
        Returns:
            List of document IDs
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Text query
            query_embedding: Optional pre-computed embedding
            k: Number of results to return
            filter: Metadata filter
            include_metadata: Whether to include metadata
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        document_ids: List[str]
    ) -> int:
        """
        Delete documents by ID.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents deleted
        """
        pass
    
    @abstractmethod
    async def get_document(
        self,
        document_id: str
    ) -> Optional[VectorDocument]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        pass
    
    @abstractmethod
    async def update_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            metadata: New metadata
            
        Returns:
            True if updated, False if not found
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        pass


class VectorStoreFactory(ABC):
    """Factory for creating vector stores."""
    
    @abstractmethod
    async def create_store(self, config: Dict[str, Any]) -> VectorStore:
        """Create a vector store from configuration."""
        pass
