"""
Contracts for Smart Ingest layer.
Based on ARCHITECTURE_V3 design.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from src.core.types import DocumentFormat


@dataclass
class ParsedDocument:
    """Result of document parsing."""
    content: str  # Markdown content
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    original_format: DocumentFormat
    page_count: Optional[int] = None
    language: Optional[str] = None


@dataclass
class ChunkMetadata:
    """Metadata for document chunks."""
    doc_id: str
    source_path: str
    chunk_index: int
    chunk_count: int
    page: Optional[int] = None
    heading: Optional[str] = None
    heading_level: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None
    token_count: Optional[int] = None
    char_count: Optional[int] = None
    summary: Optional[str] = None
    version: str = "1.0.0"


class AbstractDocumentParser(ABC):
    """Contract for document parsers."""
    
    @abstractmethod
    async def parse(self, file_path: Path, **kwargs) -> ParsedDocument:
        """Parse document to Markdown."""
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if format is supported."""
        pass


class AbstractChunker(ABC):
    """Contract for document chunkers."""
    
    @abstractmethod
    async def chunk(self, document: ParsedDocument, **kwargs) -> List[Dict[str, Any]]:
        """Chunk document into semantic chunks."""
        pass
    
    @abstractmethod
    def calculate_optimal_size(self, document: ParsedDocument) -> tuple[int, int]:
        """Calculate optimal chunk size."""
        pass


class AbstractIngestPipeline(ABC):
    """Contract for ingest pipelines."""
    
    @abstractmethod
    async def process(
        self,
        file_path: Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> Dict[str, Any]:
        """Process document through full pipeline."""
        pass
    
    @abstractmethod
    async def batch_process(
        self,
        file_paths: List[Path],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process multiple documents."""
        pass
