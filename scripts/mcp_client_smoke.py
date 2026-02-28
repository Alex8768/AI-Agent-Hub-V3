import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mcp_protocol.client.filesystem_client import FilesystemClient


async def main():
    client = FilesystemClient()
    try:
        await client.connect()
        
        # Список инструментов
        tools = await client.list_tools()
        print("Available tools:", tools)
        
        # Прочитаем текущую директорию
        files = await client.list_files(".", recursive=False)
        print("Files in current dir:", files[:5])  # первые 5
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
