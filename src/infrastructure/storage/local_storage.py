from __future__ import annotations

import asyncio
import os
import aiofiles
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.core.config import settings

from src.security.workspace_guard import WorkspaceGuard, WorkspaceAccessError


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    path: Path
    size_bytes: int


class LocalStorage:
    """Async local filesystem storage for Base.

    Root: <root_dir>/uploads_root (default settings.data_dir / "uploads")
    Security:
    - Never allow reading/writing/deleting outside uploads_root
    - storage_key may be relative (preferred) or absolute (legacy/tests), but absolute must be inside uploads_root
    """

    def __init__(self, root_dir: str | None = None):
        self.root = Path(root_dir) if root_dir else (settings.data_dir / "uploads")
        self.root.mkdir(parents=True, exist_ok=True)

        # canonical roots
        self.uploads_root = self.root.resolve()
        self.data_root = Path(settings.data_dir).resolve()

        # WorkspaceGuard base_dir points to uploads_root so workspace_root(workspace_id) == uploads_root/<ws>
        self._guard = WorkspaceGuard(base_dir=self.uploads_root)
    def _resolve_path(self, storage_key: str) -> Path:
        """Resolve storage_key to an absolute path safely (inside uploads_root).

        Supports:
        - Absolute legacy paths (allowed only if inside uploads_root)
        - Relative keys relative to uploads_root (preferred for tmp/test roots)
        - Relative keys relative to data_root (backward compat with 'uploads/ws/doc/file' stored under ./data)
        """
        sk = (storage_key or "").strip()
        if not sk:
            raise WorkspaceAccessError("Empty storage_key")

        pth = Path(sk)

        try:
            if pth.is_absolute():
                rp = pth.resolve()
                rp.relative_to(self.uploads_root)
                return rp

            # 1) Prefer relative-to uploads_root (works for tmp_path roots where storage_key = 'ws/doc/file')
            rp1 = (self.uploads_root / pth).resolve()
            rp1.relative_to(self.uploads_root)
            return rp1
        except Exception:
            # fall through to data_root strategy
            pass

        try:
            # 2) Backward compat: relative-to data_root (works for storage_key like 'uploads/ws/doc/file')
            rp2 = (self.data_root / pth).resolve()
            rp2.relative_to(self.uploads_root)
            return rp2
        except Exception as e:
            raise WorkspaceAccessError("storage_key escapes uploads root") from e

        # relative keys:
        # Prefer interpreting as path relative to data_root (keeps backward compat with existing keys like 'uploads/ws/doc/file')
        rp = (self.data_root / p).resolve()
        rp.relative_to(self.uploads_root)  # raises if outside
        return rp

    async def save_upload(
        self,
        workspace_id: str,
        doc_id: str,
        filename: str,
        data: bytes
    ) -> StoredObject:
        """Асинхронно сохраняет загруженный файл."""
        safe_ws = workspace_id or "default"
        dest_dir = (self.uploads_root / safe_ws / doc_id)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: dest_dir.mkdir(parents=True, exist_ok=True))

        dest_path = dest_dir / filename

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(data)

        size = dest_path.stat().st_size

        # Prefer storing relative-to data_root key (e.g., 'uploads/ws/doc/file')
        try:
            storage_key = str(dest_path.relative_to(self.data_root))
        except ValueError:
            # For non-standard roots/tests: keep relative to uploads_root if possible, else absolute
            try:
                storage_key = str(dest_path.relative_to(self.uploads_root))
            except ValueError:
                storage_key = str(dest_path)

        return StoredObject(storage_key=storage_key, path=dest_path, size_bytes=size)

    async def delete(self, storage_key: str) -> bool:
        """Асинхронно удаляет файл по storage_key."""
        try:
            p = self._resolve_path(storage_key)
        except WorkspaceAccessError:
            return False

        if not p.exists():
            return False

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: p.unlink())
        return True

    async def file_exists(self, storage_key: str) -> bool:
        """Асинхронно проверяет существование файла."""
        try:
            p = self._resolve_path(storage_key)
        except WorkspaceAccessError:
            return False

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: p.stat())
            return True
        except FileNotFoundError:
            return False

    async def get_size(self, storage_key: str) -> Optional[int]:
        """Асинхронно получает размер файла."""
        try:
            p = self._resolve_path(storage_key)
        except WorkspaceAccessError:
            return None

        loop = asyncio.get_event_loop()
        try:
            stat = await loop.run_in_executor(None, lambda: p.stat())
            return stat.st_size
        except FileNotFoundError:
            return None

    async def read_file(self, storage_key: str) -> Optional[bytes]:
        """Асинхронно читает файл."""
        try:
            p = self._resolve_path(storage_key)
        except WorkspaceAccessError:
            return None

        if not p.exists():
            return None

        async with aiofiles.open(p, "rb") as f:
            return await f.read()
