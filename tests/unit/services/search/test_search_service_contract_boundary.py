from __future__ import annotations

from pathlib import Path

from src.services.search.contracts import SearchServiceRequest, SearchServiceResult
from src.services.search import search_service


def test_search_service_module_does_not_import_api_schemas() -> None:
    content = Path(search_service.__file__).read_text(encoding="utf-8")
    assert "from src.api.schemas import" not in content


def test_search_service_contracts_match_api_shape_expectations() -> None:
    request = SearchServiceRequest.model_validate(
        {
            "query": "hello",
            "k": 5,
            "include_content": False,
            "include_metadata": True,
        }
    )
    assert request.query == "hello"
    assert request.k == 5

    result = SearchServiceResult.model_validate(
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "score": 0.9,
            "snippet": "s",
            "metadata": {},
        }
    )
    assert result.chunk_id == "c1"
    assert result.document_id == "d1"
