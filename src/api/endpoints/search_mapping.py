from __future__ import annotations

from typing import Any

from src.api.schemas import HybridSearchResponse, SearchRequest, SearchResult
from src.services.search.contracts import SearchServiceRequest


def to_service_request(request: SearchRequest) -> SearchServiceRequest:
    return SearchServiceRequest.model_validate(request.model_dump())


def to_api_search_results(rows: list[Any] | None) -> list[SearchResult]:
    return [
        SearchResult.model_validate(row.model_dump() if hasattr(row, "model_dump") else row, from_attributes=True)
        for row in list(rows or [])
    ]


def to_hybrid_search_response(payload: Any) -> HybridSearchResponse:
    if not isinstance(payload, dict):
        return HybridSearchResponse()

    graph = payload.get("graph")
    evidence = payload.get("evidence")
    stats = payload.get("stats")

    return HybridSearchResponse(
        results=to_api_search_results(payload.get("results")),
        graph=(graph if isinstance(graph, dict) else {}),
        evidence=(evidence if isinstance(evidence, list) else []),
        stats=(stats if isinstance(stats, dict) else {}),
    )
