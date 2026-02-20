#!/usr/bin/env python3
"""
MCP Filesystem Server for AI Agent Hub V3.
Provides file system operations through MCP protocol.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from mcp import Client, Server
from mcp.types import Tool, TextContent

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
        
        @self.server.tool(
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
        )
        async def list_files(path: str, recursive: bool = False) -> str:
            """List files in directory."""
            try:
                # Validate path is within workspace
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
        
        @self.server.tool(
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
        )
        async def read_file(path: str, encoding: str = "utf-8") -> str:
            """Read file contents."""
            try:
                safe_path = self.guard.safe_path_root(settings.workspace_root_path, path)
                
                if not safe_path.exists():
                    return f"File does not exist: {path}"
                
                if not safe_path.is_file():
                    return f"Not a file: {path}"
                
                # Check file size limit (10MB)
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
        
        @self.server.tool(
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
        )
        async def write_file(
            path: str,
            content: str,
            encoding: str = "utf-8",
            overwrite: bool = False
        ) -> str:
            """Write content to file."""
            try:
                safe_path = self.guard.safe_path_root(settings.workspace_root_path, path)
                
                if safe_path.exists() and not overwrite:
                    return f"File already exists: {path}. Use overwrite=true to replace."
                
                # Ensure directory exists
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
        """Run the MCP server."""
        async with self.server.run() as session:
            # Server is now running and accepting connections
            print(f"📁 MCP Filesystem Server running")
            print(f"📁 Workspace root: {settings.workspace_root_path}")
            
            # Keep server alive
            await asyncio.Future()


async def main():
    """Main entry point."""
    server = FilesystemMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
