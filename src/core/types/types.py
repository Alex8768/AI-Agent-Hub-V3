# 📄 ФАЙЛ: src/core/types.py
"""
Core type definitions for AI Agent Hub V3.
Defines foundational data structures for the entire system.
ARCHITECTURE_V3: Core Layer - Data Types and Models
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import uuid


# ============ CORE ENUMS ============
class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING_TOOL = "executing_tool"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Roles in conversation messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


class MessageType(str, Enum):
    """Types of messages in the system."""
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class ProcessingState(str, Enum):
    """State of async processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============ BASE MODELS ============
class TimestampedModel(BaseModel):
    """Base model with timestamps and ID."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
        protected_namespaces=()
    )


class NamedModel(TimestampedModel):
    """Model with a name."""
    name: str
    description: Optional[str] = None


# ============ MESSAGE MODELS ============
class ToolCall(BaseModel):
    """Represents a call to a tool."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None


class Message(BaseModel):
    """Core message structure for agent communication."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    type: MessageType = MessageType.TEXT
    
    # Message metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Tool interactions
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_call_id: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokens: Optional[int] = None
    model: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "msg_123",
                "role": "user",
                "content": "Hello, agent!",
                "type": "text",
                "session_id": "session_456",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class MessageHistory(BaseModel):
    """History of messages in a conversation."""
    messages: List[Message] = Field(default_factory=list)
    max_messages: Optional[int] = 100
    
    def add_message(self, message: Message) -> None:
        """Add a message to history."""
        self.messages.append(message)
        if self.max_messages and len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_conversation_text(self) -> str:
        """Get conversation as formatted text."""
        lines = []
        for msg in self.messages:
            lines.append(f"{msg.role.value.upper()}: {msg.content}")
        return "\n".join(lines)


# ============ AGENT STATE MODELS ============
class AgentState(BaseModel):
    """Complete state of an agent."""
    # Identification
    agent_id: str
    session_id: str
    
    # Status
    status: AgentStatus = AgentStatus.IDLE
    current_node: Optional[str] = None
    current_tool: Optional[str] = None
    
    # Data
    messages: MessageHistory = Field(default_factory=MessageHistory)
    context: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution
    execution_stack: List[str] = Field(default_factory=list)
    visited_nodes: List[str] = Field(default_factory=list)
    
    # Errors
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_error(self, error: str) -> None:
        """Add an error to state."""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {error}")
        self.status = AgentStatus.ERROR
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to state."""
        self.warnings.append(f"{datetime.utcnow().isoformat()}: {warning}")


class AgentSession(TimestampedModel):
    """Persistent agent session."""
    session_id: str
    user_id: Optional[str] = None
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    current_state: Optional[AgentState] = None
    is_active: bool = True
    
    # Statistics
    total_messages: int = 0
    total_tokens: int = 0
    total_tool_calls: int = 0


# ============ TASK MODELS ============
class Task(TimestampedModel):
    """Represents an agent task."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    
    # Task definition
    goal: str
    instructions: Optional[str] = None
    expected_output: Optional[str] = None
    
    # Execution
    status: ProcessingState = ProcessingState.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Metadata
    priority: int = 1  # 1-10, higher is more important
    timeout_seconds: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskGraph(BaseModel):
    """Graph of dependent tasks."""
    tasks: Dict[str, Task] = Field(default_factory=dict)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    
    def add_task(self, task: Task, dependencies: Optional[List[str]] = None) -> None:
        """Add a task to the graph."""
        self.tasks[task.task_id] = task
        if dependencies:
            self.dependencies[task.task_id] = dependencies


# ============ CONFIGURATION TYPES ============
class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: str  # "openai", "anthropic", "ollama", "google"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30


    max_retries: Optional[int] = None
class VectorStoreConfig(BaseModel):
    """Configuration for vector stores."""
    provider: str  # "faiss", "qdrant", "chroma"
    path: str
    index_name: Optional[str] = None
    dimension: Optional[int] = None
    similarity_metric: str = "cosine"


class MCPConfig(BaseModel):
    """Configuration for MCP servers."""
    enabled: bool = False
    servers: List[Dict[str, str]] = Field(default_factory=list)
    max_tools_per_server: int = 10


# ============ TYPE ALIASES ============
AgentID = str
SessionID = str
TaskID = str
MessageID = str
WorkspaceID = str
UserID = str
ToolName = str
ModelName = str

# Type-safe dictionaries
MessageDict = Dict[MessageID, Message]
AgentStateDict = Dict[AgentID, AgentState]
TaskDict = Dict[TaskID, Task]