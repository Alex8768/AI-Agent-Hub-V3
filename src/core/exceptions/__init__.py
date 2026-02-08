# 📄 ФАЙЛ: src/core/exceptions/__init__.py
"""
Exceptions module for AI Agent Hub V3.
"""

# Реэкспортируем все исключения из exceptions.py
from .exceptions import (
    HubError,
    ConfigurationError,
    EnvironmentError,
    ValidationError,
    ProviderError,
    LLMError,
    VectorStoreError,
    EmbeddingError,
    MCPError,
    ToolExecutionError,
    ToolNotFoundError,
    AgentError,
    AgentExecutionError,
    StateTransitionError,
    GraphExecutionError,
    WorkspaceError,
    SecurityError,
    wrap_exception,
    create_error_context,
)

__all__ = [
    "HubError",
    "ConfigurationError",
    "EnvironmentError",
    "ValidationError",
    "ProviderError",
    "LLMError",
    "VectorStoreError",
    "EmbeddingError",
    "MCPError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "AgentError",
    "AgentExecutionError",
    "StateTransitionError",
    "GraphExecutionError",
    "WorkspaceError",
    "SecurityError",
    "wrap_exception",
    "create_error_context",
]