from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable
# ============ AGENT CONTRACTS = ============
class Agent(Configurable, Initializable, HealthCheckable, ABC):
    """Contract for agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Agent identifier."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description."""
        pass
    
    @abstractmethod
    async def process(
        self,
        input_message: Any,
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an input message.
        
        Args:
            input_message: Input message from user or system
            session_state: Current agent state (optional)
            
        Returns:
            Updated agent state
        """
        pass
    
    @abstractmethod
    async def process_stream(
        self,
        input_message: Any,
        session_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process an input message with streaming.
        
        Args:
            input_message: Input message from user or system
            session_state: Current agent state (optional)
            
        Yields:
            Stream events
        """
        pass
    
    @abstractmethod
    async def reset(self, session_id: str) -> None:
        """Reset agent state for a session."""
        pass


class AgentFactory(ABC):
    """Factory for creating agents."""
    
    @abstractmethod
    async def create_agent(
        self,
        agent_config: Dict[str, Any]
    ) -> Agent:
        """Create an agent from configuration."""
        pass
