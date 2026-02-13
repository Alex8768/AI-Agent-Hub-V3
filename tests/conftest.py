"""
Pytest configuration for AI Agent Hub V3 tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

from src.core.config import settings


# Configure test settings
@pytest.fixture(scope="session", autouse=True)
def set_test_settings():
    """Set test settings."""
    settings.environment = "test"
    settings.debug = True
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.llm_provider = "mock"  # Use mock LLM for tests
    yield


# Event loop fixture
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# Async fixtures
@pytest_asyncio.fixture(scope="function")
async def mock_llm_provider():
    """Mock LLM provider for tests."""
    mock = AsyncMock()
    mock.generate.return_value = {
        "content": "Mocked LLM response",
        "model": "mock-model",
        "provider": "mock",
        "tokens_used": 10,
        "finish_reason": "stop",
        "metadata": {}
    }
    
    async def mock_stream():
        yield "Mocked "
        yield "streaming "
        yield "response"
    
    mock.generate_stream.return_value = mock_stream()
    return mock


@pytest_asyncio.fixture(scope="function")
async def mock_vector_store():
    """Mock vector store for tests."""
    mock = AsyncMock()
    mock.search.return_value = [
        {
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "content": "Test content 1",
            "score": 0.9,
            "metadata": {"source": "test"}
        }
    ]
    mock.add_chunks.return_value = ["chunk_1", "chunk_2"]
    mock.get_statistics.return_value = {"total_chunks": 2}
    return mock


@pytest_asyncio.fixture(scope="function")
async def mock_document_processor():
    """Mock document processor for tests."""
    mock = AsyncMock()
    mock.process.return_value = {
        "document_id": "doc_1",
        "chunks": [
            {
                "id": "chunk_1",
                "content": "Test chunk 1",
                "metadata": {"page": 1}
            }
        ],
        "metadata": {"title": "Test Document"}
    }
    mock.supports.return_value = True
    return mock


# Test data fixtures
@pytest.fixture
def sample_document():
    """Sample document data for tests."""
    return {
        "id": "doc_123",
        "name": "test.pdf",
        "path": "/tmp/test.pdf",
        "format": "pdf",
        "size": 1024,
        "status": "completed",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author"
        }
    }


@pytest.fixture
def sample_chunks():
    """Sample document chunks for tests."""
    return [
        {
            "id": "chunk_1",
            "document_id": "doc_123",
            "content": "This is the first chunk.",
            "chunk_index": 0,
            "chunk_count": 2,
            "token_count": 10,
            "metadata": {"page": 1}
        },
        {
            "id": "chunk_2",
            "document_id": "doc_123",
            "content": "This is the second chunk.",
            "chunk_index": 1,
            "chunk_count": 2,
            "token_count": 10,
            "metadata": {"page": 2}
        }
    ]


@pytest.fixture
def sample_search_request():
    """Sample search request for tests."""
    return {
        "query": "test query",
        "k": 5,
        "filters": {"document_type": "test"},
        "include_metadata": True
    }


# Cleanup fixtures
@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Cleanup logic here
    pass
