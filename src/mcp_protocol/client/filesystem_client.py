import asyncio
import json
from typing import Dict, Any, List, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


class FilesystemClient:
    """Client for filesystem MCP server."""
    
    def __init__(self, server_script: str = "mcp_servers/filesystem/server.py"):
        self.server_script = server_script
        self.session: Optional[ClientSession] = None
        self._stdio = None
    
    async def connect(self):
        """Connect to the filesystem server."""
        # Создаём параметры сервера
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script]
        )
        
        # stdio_client принимает параметры сервера
        self._stdio = stdio_client(server_params)
        read_stream, write_stream = await self._stdio.__aenter__()
        
        # Создаём сессию
        self.session = await ClientSession(read_stream, write_stream).__aenter__()
        await self.session.initialize()
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._stdio:
            await self._stdio.__aexit__(None, None, None)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        if not self.session:
            raise RuntimeError("Not connected")
        result = await self.session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]
    
    async def list_files(self, path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """List files in directory."""
        if not self.session:
            raise RuntimeError("Not connected")
        result = await self.session.call_tool(
            "list_files",
            {"path": path, "recursive": recursive}
        )
        # result.content[0].text содержит JSON
        data = json.loads(result.content[0].text)
        return data.get("items", [])
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents."""
        if not self.session:
            raise RuntimeError("Not connected")
        result = await self.session.call_tool(
            "read_file",
            {"path": path, "encoding": encoding}
        )
        data = json.loads(result.content[0].text)
        return data.get("content", "")
    
    async def write_file(self, path: str, content: str, overwrite: bool = False) -> bool:
        """Write file contents."""
        if not self.session:
            raise RuntimeError("Not connected")
        result = await self.session.call_tool(
            "write_file",
            {"path": path, "content": content, "overwrite": overwrite}
        )
        return "successfully" in result.content[0].text.lower()
