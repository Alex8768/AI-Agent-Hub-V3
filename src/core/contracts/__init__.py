# 📄 ФАЙЛ: src/core/contracts/__init__.py
"""
Core contracts (abstract interfaces) for AI Agent Hub V3.
ARCHITECTURE_V3: Core Layer - Contracts and Interfaces
"""

from .contracts import (
    # Core contracts
    Configurable,
    Initializable,
    HealthCheckable,
    
    # Embedding contracts
    EmbeddingModel,
    EmbeddingFactory,
    
    # LLM contracts
    LLMProvider,
    LLMProviderFactory,
    LLMCompletion,
    LLMChunk,
    
    # Vector store contracts
    VectorStore,
    VectorStoreFactory,
    VectorDocument,
    SearchResult,
    
    # MCP contracts
    MCPTool,
    MCPServer,
    MCPClient,
    ToolDefinition,
    ToolResult,
    
    # Agent contracts
    Agent,
    AgentFactory,
    
    # Workspace contracts
    Workspace,
    
    # Observability contracts
    Logger,
    MetricsCollector,
    Tracer,
)

__all__ = [
    # Core contracts
    "Configurable",
    "Initializable",
    "HealthCheckable",
    
    # Embedding contracts
    "EmbeddingModel",
    "EmbeddingFactory",
    
    # LLM contracts
    "LLMProvider",
    "LLMProviderFactory",
    "LLMCompletion",
    "LLMChunk",
    
    # Vector store contracts
    "VectorStore",
    "VectorStoreFactory",
    "VectorDocument",
    "SearchResult",
    
    # MCP contracts
    "MCPTool",
    "MCPServer",
    "MCPClient",
    "ToolDefinition",
    "ToolResult",
    
    # Agent contracts
    "Agent",
    "AgentFactory",
    
    # Workspace contracts
    "Workspace",
    
    # Observability contracts
    "Logger",
    "MetricsCollector",
    "Tracer",
]