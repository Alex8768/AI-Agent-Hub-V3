#!/usr/bin/env python3
"""
MCP Filesystem Server for AI Agent Hub V3.
Provides file system operations through MCP protocol.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ListToolsResult,
    CallToolResult,
)

from src.core.config import settings
from src.security.workspace_guard import WorkspaceGuard


class FilesystemMCPServer:
    """MCP server providing filesystem operations."""
    
    def __init__(self):
        self.server = Server("filesystem")
        self.guard = WorkspaceGuard()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup filesystem tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="list_files",
                        description="List files and directories in a path",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to list (relative to workspace root)"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "List recursively",
                                    "default": False
                                }
                            },
                            "required": ["path"]
                        }
                    ),
                    Tool(
                        name="read_file",
                        description="Read contents of a file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to file (relative to workspace root)"
                                },
                                "encoding": {
                                    "type": "string",
                                    "description": "File encoding",
                                    "default": "utf-8"
                                }
                            },
                            "required": ["path"]
                        }
                    ),
                    Tool(
                        name="write_file",
                        description="Write content to a file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to file (relative to workspace root)"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content to write"
                                },
                                "encoding": {
                                    "type": "string",
                                    "description": "File encoding",
                                    "default": "utf-8"
                                },
                                "overwrite": {
                                    "type": "boolean",
                                    "description": "Overwrite if file exists",
                                    "default": False
                                }
                            },
                            "required": ["path", "content"]
                        }
                    ),
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            if name == "list_files":
                result = await self._list_files(**arguments)
                return CallToolResult(content=[TextContent(type="text", text=result)])
            elif name == "read_file":
                result = await self._read_file(**arguments)
                return CallToolResult(content=[TextContent(type="text", text=result)])
            elif name == "write_file":
                result = await self._write_file(**arguments)
                return CallToolResult(content=[TextContent(type="text", text=result)])
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True
                )
    
    async def _list_files(self, path: str, recursive: bool = False) -> str:
        """List files in directory."""
        try:
            safe_path = self.guard.safe_path_root(settings.workspace_root_path, path)
            
            if not safe_path.exists():
                return f"Path does not exist: {path}"
            
            if not safe_path.is_dir():
                return f"Not a directory: {path}"
            
            results = []
            if recursive:
                for item in safe_path.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(safe_path)
                        results.append({
                            "name": item.name,
                            "path": str(rel_path),
                            "type": "file",
                            "size": item.stat().st_size,
                            "modified": item.stat().st_mtime
                        })
            else:
                for item in safe_path.iterdir():
                    results.append({
                        "name": item.name,
                        "path": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                        "modified": item.stat().st_mtime
                    })
            
            return json.dumps({
                "path": path,
                "items": results,
                "count": len(results)
            }, indent=2)
            
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    async def _read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents."""
        try:
            safe_path = self.guard.safe_path_root(settings.workspace_root_path, path)
            
            if not safe_path.exists():
                return f"File does not exist: {path}"
            
            if not safe_path.is_file():
                return f"Not a file: {path}"
            
            if safe_path.stat().st_size > 10 * 1024 * 1024:
                return f"File too large: {safe_path.stat().st_size} bytes (limit: 10MB)"
            
            content = safe_path.read_text(encoding=encoding)
            return json.dumps({
                "path": path,
                "size": len(content),
                "content": content
            }, indent=2)
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def _write_file(self, path: str, content: str, encoding: str = "utf-8", overwrite: bool = False) -> str:
        """Write content to file."""
        try:
            safe_path = self.guard.safe_path_root(settings.workspace_root_path, path)
            
            if safe_path.exists() and not overwrite:
                return f"File already exists: {path}. Use overwrite=true to replace."
            
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding=encoding)
            
            return json.dumps({
                "path": path,
                "size": len(content),
                "message": "File written successfully"
            }, indent=2)
            
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    async def run(self):
        """Run the MCP server with stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = FilesystemMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
