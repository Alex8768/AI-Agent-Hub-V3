"""
Contracts for Export Layer.
Based on ARCHITECTURE_V3 design.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, BinaryIO, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from src.core.types import ExportFormat


@dataclass
class ExportOptions:
    """Export options."""
    include_citations: bool = True
    include_metadata: bool = True
    style_template: Optional[str] = None
    watermark: Optional[str] = None
    page_numbers: bool = True
    table_of_contents: bool = False
    language: str = "en"
    author: Optional[str] = None
    title: Optional[str] = None
    margin_top: float = 2.54  # cm
    margin_bottom: float = 2.54
    margin_left: float = 2.54
    margin_right: float = 2.54


@dataclass
class ExportContent:
    """Content for export."""
    title: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    citations: List[Dict[str, Any]]
    attachments: Optional[List[Dict[str, Any]]] = None
    styles: Optional[Dict[str, Any]] = None
    templates: Optional[Dict[str, str]] = None


class AbstractExporter(ABC):
    """Contract for exporters."""
    
    @abstractmethod
    async def export(
        self,
        content: ExportContent,
        output_path: Path,
        options: Optional[ExportOptions] = None
    ) -> Path:
        """Export content to file."""
        pass
    
    @abstractmethod
    async def export_to_bytes(
        self,
        content: ExportContent,
        options: Optional[ExportOptions] = None
    ) -> bytes:
        """Export content to bytes."""
        pass
    
    @abstractmethod
    async def export_to_stream(
        self,
        content: ExportContent,
        stream: BinaryIO,
        options: Optional[ExportOptions] = None
    ) -> None:
        """Export content to stream."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[ExportFormat]:
        """Supported export formats."""
        pass
    
    @abstractmethod
    def validate_content(self, content: ExportContent) -> List[str]:
        """Validate content before export."""
        pass
    
    @abstractmethod
    async def get_templates(self) -> List[str]:
        """Get available templates."""
        pass


class AbstractExportManager(ABC):
    """Contract for export managers."""
    
    @abstractmethod
    async def export(
        self,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        format: ExportFormat,
        template: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Export content."""
        pass
    
    @abstractmethod
    async def batch_export(
        self,
        items: List[Dict[str, Any]],
        format: ExportFormat,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Export multiple items."""
        pass
    
    @abstractmethod
    async def register_exporter(
        self,
        format: ExportFormat,
        exporter: AbstractExporter
    ) -> None:
        """Register custom exporter."""
        pass
    
    @abstractmethod
    async def get_export_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get export history."""
        pass
