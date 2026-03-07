"""Тесты для исправленного IngestService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.document.ingest_service import IngestService, Chunk, DocumentFormat, IngestResult
from src.core.exceptions import EmbeddingError, ValidationError
from src.adapters.embedding import get_embedding_factory


@pytest.fixture
def mock_vector_store():
    store = AsyncMock()
    store.add_documents.return_value = ["chunk1"]
    store.get_stats.return_value = {"total_vectors": 1}
    store.health_check.return_value = {"status": "healthy"}
    return store


@pytest.fixture
def ingest_service(mock_vector_store):
    # IngestService теперь принимает только vector_store
    return IngestService(
        vector_store=mock_vector_store,
        chunk_size=100,
        chunk_overlap=20
    )


@pytest.mark.asyncio
async def test_workspace_id_not_overwritten(ingest_service):
    """Тест: workspace_id из metadata не должен перетираться."""
    result = await ingest_service.ingest_text(
        text="test content",
        filename="test.txt",
        metadata={"workspace_id": "custom_ws_123", "source": "test"}
    )
    
    assert result.metadata.get("workspace_id") == "custom_ws_123"
    assert result.metadata.get("source") == "test"
    assert result.success is True


@pytest.mark.asyncio
async def test_workspace_id_default_when_missing(ingest_service):
    """Тест: если workspace_id нет в metadata, ставится 'default'."""
    result = await ingest_service.ingest_text(
        text="test content",
        filename="test.txt",
        metadata={"source": "test"}
    )
    
    assert result.metadata.get("workspace_id") == "default"
    assert result.metadata.get("source") == "test"
    assert result.success is True


@pytest.mark.asyncio
async def test_embedding_failure_fast(ingest_service, monkeypatch):
    """Тест: при ошибке эмбеддинга - никаких частичных сохранений."""
    # Мокаем embed_documents чтобы он падал
    async def mock_embed(*args, **kwargs):
        raise Exception("Embedding failed")
    
    monkeypatch.setattr(
        'src.adapters.embedding.sentence_transformer_adapter.SentenceTransformerAdapter.embed_documents',
        mock_embed
    )
    
    result = await ingest_service.ingest_text(
        text="test content " * 100,
        filename="test.txt"
    )
    
    assert result.success is False
    assert "Embedding failed" in result.errors[0]
    assert ingest_service._vector_store.add_documents.call_count == 0


@pytest.mark.asyncio
async def test_error_preserves_context(ingest_service, monkeypatch):
    """Тест: при ошибке сохраняем максимум информации."""
    async def mock_embed(*args, **kwargs):
        raise Exception("Embedding failed")
    
    monkeypatch.setattr(
        'src.adapters.embedding.sentence_transformer_adapter.SentenceTransformerAdapter.embed_documents',
        mock_embed
    )
    
    text = "test content"
    result = await ingest_service.ingest_text(
        text=text,
        filename="test.txt",
        metadata={"source": "test", "user": "alex"}
    )
    
    assert result.filename == "test.txt"
    assert result.metadata.get("source") == "test"
    assert result.metadata.get("user") == "alex"
    assert str(len(text)) == str(result.metadata.get("text_length", 0))


@pytest.mark.asyncio
async def test_empty_text_validation(ingest_service):
    """Тест: пустой текст вызывает ValidationError."""
    with pytest.raises(ValidationError):
        await ingest_service.ingest_text(
            text="   ",
            filename="test.txt"
        )


@pytest.mark.asyncio
async def test_chunking_preserves_metadata(ingest_service):
    """Тест: чанкинг сохраняет метаданные."""
    text = "First sentence. Second sentence. Third sentence."
    result = await ingest_service.ingest_text(
        text=text,
        filename="test.txt",
        metadata={"source": "test", "language": "en"}
    )
    
    assert result.success is True
    assert result.metadata.get("source") == "test"
    assert result.metadata.get("language") == "en"
    assert result.total_chunks > 0


@pytest.mark.asyncio
async def test_document_format_detection(ingest_service):
    """Тест: определение формата по расширению."""
    test_cases = [
        ("doc.txt", DocumentFormat.TXT),
        ("doc.md", DocumentFormat.MD),
        ("doc.pdf", DocumentFormat.PDF),
        ("doc.docx", DocumentFormat.DOCX),
        ("doc.DOCX", DocumentFormat.DOCX),
        ("doc.html", DocumentFormat.HTML),
        ("doc.htm", DocumentFormat.HTML),
        ("doc.unknown", DocumentFormat.UNKNOWN),
    ]
    
    for filename, expected_format in test_cases:
        result = await ingest_service.ingest_text(
            text="test",
            filename=filename
        )
        assert result.format == expected_format, f"Failed for {filename}"


def test_prepare_ingest_metadata_boundary_preserves_defaults(ingest_service):
    fmt, meta = ingest_service._prepare_ingest_metadata_boundary(
        metadata={"source": "unit"},
        filename="doc.txt",
        text_length=12,
        document_id="doc-1",
    )
    assert fmt == DocumentFormat.TXT
    assert meta.get("filename") == "doc.txt"
    assert meta.get("format") == "txt"
    assert meta.get("text_length") == 12
    assert meta.get("document_id") == "doc-1"
    assert meta.get("workspace_id") == "default"
    assert meta.get("source") == "unit"
