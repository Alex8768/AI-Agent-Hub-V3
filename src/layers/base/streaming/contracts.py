"""
Contracts for Process Streaming layer.
Based on ARCHITECTURE_V3 design.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import time
import json


class ThoughtType(Enum):
    """Types of agent thoughts."""
    REASONING = "reasoning"
    DECISION = "decision"
    TOOL_SELECTION = "tool_selection"
    TOOL_EXECUTION = "tool_execution"
    ERROR = "error"
    COMPLETION = "completion"
    PROGRESS = "progress"
    QUESTION = "question"


@dataclass
class ThoughtEvent:
    """Agent thought event for streaming."""
    id: str
    session_id: str
    thought_type: ThoughtType
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_thought_id: Optional[str] = None
    depth: int = 0
    
    def to_sse_format(self) -> str:
        """Format for Server-Sent Events."""
        event_data = {
            "id": self.id,
            "event": "thought",
            "data": {
                "type": self.thought_type.value,
                "content": self.content,
                "timestamp": self.timestamp,
                "metadata": self.metadata,
                "depth": self.depth,
                "session_id": self.session_id,
            }
        }
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "thought_type": self.thought_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "parent_thought_id": self.parent_thought_id,
            "depth": self.depth,
        }


class AbstractStreamPublisher(ABC):
    """Contract for stream publishers."""
    
    @abstractmethod
    async def publish(self, session_id: str, event: ThoughtEvent) -> None:
        """Publish event to stream."""
        pass
    
    @abstractmethod
    async def publish_batch(self, session_id: str, events: List[ThoughtEvent]) -> None:
        """Publish multiple events."""
        pass
    
    @abstractmethod
    async def subscribe(self, session_id: str) -> AsyncGenerator[ThoughtEvent, None]:
        """Subscribe to session events."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, session_id: str) -> None:
        """Unsubscribe from session."""
        pass
    
    @abstractmethod
    async def get_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history."""
        pass
    
    @abstractmethod
    def get_subscriber_count(self, session_id: str) -> int:
        """Get number of subscribers."""
        pass


class AbstractStreamingWrapper(ABC):
    """Contract for streaming wrappers."""
    
    @abstractmethod
    async def run_with_streaming(
        self,
        agent_func,
        initial_state: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Run agent function with streaming."""
        pass
    
    @abstractmethod
    def wrap_function(
        self,
        func,
        function_name: str,
        session_id: str
    ):
        """Wrap function for streaming."""
        pass
