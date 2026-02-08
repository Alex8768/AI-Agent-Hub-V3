"""
Core contracts (abstract interfaces) for AI Agent Hub V3.
Defines the architectural boundaries between components.
ARCHITECTURE_V3: Core Layer - Contracts and Interfaces
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass


# ============ CORE CONTRACTS ============
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


# ============ EMBEDDING CONTRACTS ============
class EmbeddingModel(Configurable, HealthCheckable, ABC):
    """
    Contract for embedding models with asymmetric search support.
    Optimized for advanced RAG systems with query/document separation.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the embedding model."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimension of embeddings (vector size)."""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Maximum tokens per input text."""
        pass
    
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query/sentence.
        May add query-specific prefixes for asymmetric search models.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        pass
    
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents/sentences with batch optimization.
        Optimized for GPU/NPU parallel processing.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass


class EmbeddingFactory(ABC):
    """Factory for creating embedding models."""
    
    @abstractmethod
    async def create_embedding_model(
        self,
        provider_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> EmbeddingModel:
        """
        Create an embedding model from configuration.
        
        Args:
            provider_type: Type of embedding provider
            config: Configuration dictionary
            
        Returns:
            EmbeddingModel instance
        """
        pass
    
    @abstractmethod
    async def get_available_providers(self) -> List[str]:
        """Get list of available provider types."""
        pass


# ============ LLM CONTRACTS ============
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
        messages: List[Any],  # Используем Any вместо конкретного типа Message
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
        messages: List[Any],
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


# ============ VECTOR STORE CONTRACTS ============
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


# ============ MCP CONTRACTS ============
@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = None
    
    def __post_init__(self):
        if self.required is None:
            self.required = []


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MCPTool(ABC):
    """Contract for MCP tools."""
    
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute the tool with given arguments.
        
        Args:
            arguments: Tool arguments
            context: Execution context
            
        Returns:
            ToolResult
        """
        pass


class MCPServer(Configurable, Initializable, HealthCheckable, ABC):
    """Contract for MCP servers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Server name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Server version."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[ToolDefinition]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute a specific tool.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Execution context
            
        Returns:
            ToolResult
        """
        pass
    
    @abstractmethod
    async def register_tool(self, tool: MCPTool) -> bool:
        """Register a new tool."""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        pass


class MCPClient(Configurable, Initializable, HealthCheckable, ABC):
    """Contract for MCP clients."""
    
    @abstractmethod
    async def connect_to_server(
        self,
        server_config: Dict[str, Any]
    ) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            server_config: Server configuration
            
        Returns:
            True if connected successfully
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from server."""
        pass
    
    @abstractmethod
    async def get_available_tools(self) -> List[ToolDefinition]:
        """Get tools from connected server."""
        pass
    
    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Call a tool on the connected server.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            
        Returns:
            ToolResult
        """
        pass


# ============ AGENT CONTRACTS ============
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


# ============ WORKSPACE CONTRACTS ============
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


# ============ OBSERVABILITY CONTRACTS ============
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