"""
Exception hierarchy for AI Agent Hub V3.
Provides structured error handling across all system layers.
ARCHITECTURE_V3: Core Layer - Error Handling
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class HubError(Exception):
    """
    Base exception for all AI Agent Hub errors.
    All custom exceptions should inherit from this.
    """
    message: str
    error_code: str = "HUB_ERROR"
    details: Optional[Dict[str, Any]] = None
    original_exception: Optional[Exception] = None
    
    def __post_init__(self):
        super().__init__(self.message)
        if self.details is None:
            self.details = {}
    
    def __str__(self) -> str:
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base += f" | Details: {details_str}"
        if self.original_exception:
            base += f" | Original: {type(self.original_exception).__name__}: {str(self.original_exception)}"
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }


# ============ CONFIGURATION ERRORS ============
@dataclass
class ConfigurationError(HubError):
    """Errors related to configuration."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class EnvironmentError(ConfigurationError):
    """Errors related to environment variables."""
    
    def __init__(
        self,
        message: str,
        env_var: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if env_var:
            details["env_var"] = env_var
        
        super().__init__(
            message=message,
            config_key=env_var,
            error_code="ENVIRONMENT_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class ValidationError(ConfigurationError):
    """Errors related to data validation."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        if expected:
            details["expected"] = expected
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


# ============ PROVIDER ERRORS ============
@dataclass
class ProviderError(HubError):
    """Base error for all provider-related errors."""
    
    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        provider_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if provider_name:
            details["provider_name"] = provider_name
        if provider_type:
            details["provider_type"] = provider_type
        
        super().__init__(
            message=message,
            error_code="PROVIDER_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class LLMError(ProviderError):
    """Errors related to LLM operations."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        tokens_used: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model:
            details["model"] = model
        if prompt:
            # Truncate long prompts in error details
            details["prompt"] = prompt[:100] + "..." if len(prompt) > 100 else prompt
        if tokens_used:
            details["tokens_used"] = tokens_used
        
        super().__init__(
            message=message,
            provider_type="llm",
            error_code="LLM_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class VectorStoreError(ProviderError):
    """Errors related to vector store operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        document_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if document_id:
            details["document_id"] = document_id
        
        super().__init__(
            message=message,
            provider_type="vector_store",
            error_code="VECTOR_STORE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class EmbeddingError(VectorStoreError):
    """Errors related to embedding generation."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        text: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model:
            details["embedding_model"] = model
        if text:
            details["text"] = text[:50] + "..." if len(text) > 50 else text
        
        super().__init__(
            message=message,
            operation="embedding",
            error_code="EMBEDDING_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


# ============ MCP ERRORS ============
@dataclass
class MCPError(HubError):
    """Errors related to Model Context Protocol."""
    
    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if server_name:
            details["server_name"] = server_name
        if tool_name:
            details["tool_name"] = tool_name
        
        super().__init__(
            message=message,
            error_code="MCP_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class ToolExecutionError(MCPError):
    """Errors during tool execution."""
    
    def __init__(
        self,
        message: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["tool_name"] = tool_name
        if arguments:
            details["arguments"] = arguments
        
        super().__init__(
            message=message,
            tool_name=tool_name,
            error_code="TOOL_EXECUTION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class ToolNotFoundError(MCPError):
    """Tool not found in MCP server."""
    
    def __init__(
        self,
        message: str,
        tool_name: str,
        available_tools: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["tool_name"] = tool_name
        if available_tools:
            details["available_tools"] = available_tools
        
        super().__init__(
            message=message,
            tool_name=tool_name,
            error_code="TOOL_NOT_FOUND_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


# ============ AGENT ERRORS ============
@dataclass
class AgentError(HubError):
    """Errors related to agent execution."""
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        node_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if agent_id:
            details["agent_id"] = agent_id
        if session_id:
            details["session_id"] = session_id
        if node_id:
            details["node_id"] = node_id
        
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class AgentExecutionError(AgentError):
    """Errors during agent execution."""
    
    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if step:
            details["step"] = step
        if input_data:
            details["input_data"] = input_data
        
        super().__init__(
            message=message,
            error_code="AGENT_EXECUTION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class StateTransitionError(AgentError):
    """Errors during state machine transitions."""
    
    def __init__(
        self,
        message: str,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        allowed_transitions: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if from_state:
            details["from_state"] = from_state
        if to_state:
            details["to_state"] = to_state
        if allowed_transitions:
            details["allowed_transitions"] = allowed_transitions
        
        super().__init__(
            message=message,
            error_code="STATE_TRANSITION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class GraphExecutionError(AgentError):
    """Errors during LangGraph execution."""
    
    def __init__(
        self,
        message: str,
        graph_name: Optional[str] = None,
        node_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if graph_name:
            details["graph_name"] = graph_name
        if node_name:
            details["node_name"] = node_name
        
        super().__init__(
            message=message,
            error_code="GRAPH_EXECUTION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


# ============ WORKSPACE ERRORS ============
@dataclass
class WorkspaceError(HubError):
    """Errors related to workspace operations."""
    
    def __init__(
        self,
        message: str,
        workspace_id: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if workspace_id:
            details["workspace_id"] = workspace_id
        if path:
            details["path"] = path
        
        super().__init__(
            message=message,
            error_code="WORKSPACE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


@dataclass
class SecurityError(WorkspaceError):
    """Security-related workspace errors."""
    
    def __init__(
        self,
        message: str,
        violation_type: Optional[str] = None,
        attempted_action: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if violation_type:
            details["violation_type"] = violation_type
        if attempted_action:
            details["attempted_action"] = attempted_action
        
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


# ============ UTILITY FUNCTIONS ============
def wrap_exception(
    exception: Exception,
    wrapper_class: type[HubError],
    message: Optional[str] = None,
    **kwargs
) -> HubError:
    """
    Wrap any exception into a HubError hierarchy exception.
    
    Args:
        exception: Original exception
        wrapper_class: HubError subclass to wrap with
        message: Custom message (defaults to original exception message)
        **kwargs: Additional parameters for wrapper class
        
    Returns:
        Wrapped exception
    """
    if isinstance(exception, HubError):
        return exception
    
    msg = message or str(exception)
    return wrapper_class(
        message=msg,
        original_exception=exception,
        **kwargs
    )


def create_error_context(**context: Any) -> Dict[str, Any]:
    """
    Create a standardized error context dictionary.
    
    Args:
        **context: Key-value pairs for context
        
    Returns:
        Standardized context dictionary
    """
    import time
    import traceback
    
    return {
        "timestamp": time.time(),
        "traceback": traceback.format_exc(),
        **context
    }