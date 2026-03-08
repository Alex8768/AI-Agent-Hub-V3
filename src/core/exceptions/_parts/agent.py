from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .base import HubError

# ============ AGENT ERRORS ============

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
