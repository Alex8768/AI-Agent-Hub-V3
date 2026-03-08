from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable
# ============ WORKSPACE CONTRACTS = ============
class Workspace(Configurable, Initializable, ABC):
    """Contract for workspaces."""
    
    @property
    @abstractmethod
    def workspace_id(self) -> str:
        """Workspace identifier."""
        pass
    
    @abstractmethod
    async def list_files(
        self,
        path: str = "",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in workspace.
        
        Args:
            path: Path within workspace
            recursive: Whether to list recursively
            
        Returns:
            List of file information dictionaries
        """
        pass
    
    @abstractmethod
    async def read_file(
        self,
        path: str,
        encoding: str = "utf-8"
    ) -> str:
        """
        Read a file from workspace.
        
        Args:
            path: File path
            encoding: File encoding
            
        Returns:
            File content
        """
        pass
    
    @abstractmethod
    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = False
    ) -> bool:
        """
        Write a file to workspace.
        
        Args:
            path: File path
            content: File content
            encoding: File encoding
            overwrite: Whether to overwrite existing file
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file from workspace.
        
        Args:
            path: File path
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        pass
    
    @abstractmethod
    async def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get file metadata."""
        pass
