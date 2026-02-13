"""Тесты для асинхронного LocalStorage."""
import pytest
import tempfile
from pathlib import Path
from src.infrastructure.storage.local_storage import LocalStorage


@pytest.fixture
async def temp_storage():
    """Создает временное хранилище для тестов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(root_dir=tmpdir)
        yield storage


@pytest.mark.asyncio
async def test_save_and_read_file(temp_storage):
    """Тест: сохранение и чтение файла."""
    data = b"test data for async storage"
    doc_id = "test_doc_123"
    
    stored = await temp_storage.save_upload(
        workspace_id="test_ws",
        doc_id=doc_id,
        filename="test.txt",
        data=data
    )
    
    assert stored.size_bytes == len(data)
    assert doc_id in str(stored.path)
    
    # Читаем файл используя полный путь, а не storage_key
    read_data = await temp_storage.read_file(stored.storage_key)
    assert read_data == data


@pytest.mark.asyncio
async def test_delete_file(temp_storage):
    """Тест: удаление файла."""
    data = b"test data"
    
    stored = await temp_storage.save_upload(
        workspace_id="test_ws",
        doc_id="doc_to_delete",
        filename="delete.txt",
        data=data
    )
    
    exists = await temp_storage.file_exists(stored.storage_key)
    assert exists is True
    
    deleted = await temp_storage.delete(stored.storage_key)
    assert deleted is True
    
    exists = await temp_storage.file_exists(stored.storage_key)
    assert exists is False


@pytest.mark.asyncio
async def test_file_not_found(temp_storage):
    """Тест: работа с несуществующим файлом."""
    exists = await temp_storage.file_exists("non/existent/file.txt")
    assert exists is False
    
    size = await temp_storage.get_size("non/existent/file.txt")
    assert size is None
    
    data = await temp_storage.read_file("non/existent/file.txt")
    assert data is None


@pytest.mark.asyncio
async def test_workspace_isolation(temp_storage):
    """Тест: файлы разных workspace не пересекаются."""
    data = b"test"
    
    stored1 = await temp_storage.save_upload(
        workspace_id="ws1",
        doc_id="doc1",
        filename="file.txt",
        data=data
    )
    
    stored2 = await temp_storage.save_upload(
        workspace_id="ws2",
        doc_id="doc1",
        filename="file.txt",
        data=data
    )
    
    assert stored1.storage_key != stored2.storage_key
    assert "ws1" in str(stored1.path)
    assert "ws2" in str(stored2.path)
    
    # Проверяем что файлы действительно разные
    data1 = await temp_storage.read_file(stored1.storage_key)
    data2 = await temp_storage.read_file(stored2.storage_key)
    assert data1 == data
    assert data2 == data
