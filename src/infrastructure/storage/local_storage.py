from __future__ import annotations

import asyncio
import aiofiles
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    path: Path
    size_bytes: int


class LocalStorage:
    """
    Async local filesystem storage for Base.
    Root: ./data/uploads
    All file operations are async to avoid blocking event loop.
    """

    def __init__(self, root_dir: str | None = None):
        self.root = Path(root_dir or "./data/uploads")
        # Синхронное создание директории при инициализации - ок, делается один раз
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(
        self, 
        workspace_id: str, 
        doc_id: str, 
        filename: str, 
        data: bytes
    ) -> StoredObject:
        """
        Асинхронно сохраняет загруженный файл.
        """
        safe_ws = workspace_id or "default"
        dest_dir = self.root / safe_ws / doc_id
        
        # Создание директорий в потоке (может быть медленным)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: dest_dir.mkdir(parents=True, exist_ok=True))
        
        dest_path = dest_dir / filename
        
        # Асинхронная запись файла через aiofiles
        async with aiofiles.open(dest_path, 'wb') as f:
            await f.write(data)
        
        # Получаем размер файла
        size = dest_path.stat().st_size
        
        storage_key = str(dest_path.relative_to(Path("./data")))
        return StoredObject(
            storage_key=storage_key, 
            path=dest_path, 
            size_bytes=size
        )

    async def delete(self, storage_key: str) -> bool:
        """
        Асинхронно удаляет файл по storage_key.
        """
        p = Path("./data") / storage_key
        
        if not p.exists():
            return False
        
        # Удаление в потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: p.unlink())
        return True

    async def file_exists(self, storage_key: str) -> bool:
        """
        Асинхронно проверяет существование файла.
        """
        p = Path("./data") / storage_key
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: p.stat())
            return True
        except FileNotFoundError:
            return False

    async def get_size(self, storage_key: str) -> Optional[int]:
        """
        Асинхронно получает размер файла.
        """
        p = Path("./data") / storage_key
        loop = asyncio.get_event_loop()
        try:
            stat = await loop.run_in_executor(None, lambda: p.stat())
            return stat.st_size
        except FileNotFoundError:
            return None

    async def read_file(self, storage_key: str) -> Optional[bytes]:
        """
        Асинхронно читает файл.
        """
        p = Path("./data") / storage_key
        if not p.exists():
            return None
        
        async with aiofiles.open(p, 'rb') as f:
            return await f.read()
