from pathlib import Path
import pytest

from src.infrastructure.storage.local_storage import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_blocks_escape_delete(tmp_path: Path):
    storage = LocalStorage(root_dir=str(tmp_path / "uploads"))
    # storage_key пытается вылезти наружу
    assert await storage.delete("../../etc/passwd") is False


@pytest.mark.asyncio
async def test_local_storage_blocks_escape_read(tmp_path: Path):
    storage = LocalStorage(root_dir=str(tmp_path / "uploads"))
    assert await storage.read_file("../../etc/passwd") is None


@pytest.mark.asyncio
async def test_local_storage_allows_inside_root(tmp_path: Path):
    storage = LocalStorage(root_dir=str(tmp_path / "uploads"))
    ws = "ws_test"
    doc = "doc1"
    obj = await storage.save_upload(ws, doc, "a.txt", b"hello")
    assert await storage.file_exists(obj.storage_key) is True
    data = await storage.read_file(obj.storage_key)
    assert data == b"hello"
    assert await storage.delete(obj.storage_key) is True
