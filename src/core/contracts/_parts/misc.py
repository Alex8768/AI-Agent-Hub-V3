from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator
# ============ OBSERVABILITY CONTRACTS = ============
class Logger(ABC):
    """Contract for logging."""
    
    @abstractmethod
    async def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a message."""
        pass


class MetricsCollector(ABC):
    """Contract for metrics collection."""
    
    @abstractmethod
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric."""
        pass
    
    @abstractmethod
    async def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter."""
        pass


class Tracer(ABC):
    """Contract for distributed tracing."""
    
    @abstractmethod
    async def start_span(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Start a new trace span."""
        pass
    
    @abstractmethod
    async def end_span(
        self,
        span: Any,
        status: str = "OK",
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """End a trace span."""
        pass
