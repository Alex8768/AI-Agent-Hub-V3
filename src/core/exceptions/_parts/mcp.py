from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .base import HubError

# ============ MCP ERRORS ============

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
