from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from .common import Configurable, Initializable, HealthCheckable
# ============ MCP CONTRACTS = ============
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
