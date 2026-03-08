from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator
# ============ CORE CONTRACTS = ============
class Configurable(ABC):
    """Contract for configurable components."""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with given settings."""
        pass


class Initializable(ABC):
    """Contract for components that require initialization."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class HealthCheckable(ABC):
    """Contract for components that support health checks."""
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return health status."""
        pass
