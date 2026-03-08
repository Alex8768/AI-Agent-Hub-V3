from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable

from src.core.types.types import Message
# ============ LLM CONTRACTS = ============
@dataclass
class LLMCompletion:
    """Result of LLM completion."""
    content: str
    model: str
    provider: str
    tokens_used: int
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMChunk:
    """Streaming chunk from LLM."""
    content: str
    chunk_index: int
    is_final: bool = False
    finish_reason: Optional[str] = None


class LLMProvider(Configurable, HealthCheckable, ABC):
    """Contract for LLM providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider."""
        pass
    
    @property
    @abstractmethod
    def context_length(self) -> int:
        """Maximum context length in tokens."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],  # Используем Any вместо конкретного типа Message
        config: Optional[Dict[str, Any]] = None
    ) -> LLMCompletion:
        """
        Generate a completion from messages.
        
        Args:
            messages: List of messages in conversation
            config: Optional configuration overrides
            
        Returns:
            LLMCompletion object
        """
        pass
    
    @abstractmethod
    async def complete_stream(
        self,
        messages: List[Message],
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[LLMChunk, None]:
        """
        Stream a completion from messages.
        
        Args:
            messages: List of messages in conversation
            config: Optional configuration overrides
            
        Yields:
            LLMChunk objects
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass


class LLMProviderFactory(ABC):
    """Factory for creating LLM providers."""
    
    @abstractmethod
    async def create_provider(self, config: Dict[str, Any]) -> LLMProvider:
        """Create an LLM provider from configuration."""
        pass
    
    @abstractmethod
    async def get_available_providers(self) -> List[str]:
        """Get list of available provider types."""
        pass
