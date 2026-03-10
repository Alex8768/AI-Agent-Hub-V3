from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class LLMRequest(BaseModel):
    prompt: str = Field(..., description="User prompt")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    provider: Optional[str] = Field(None, description="Provider override (e.g., openai, ollama)")
    model: Optional[str] = Field(None, description="Model override")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)

class LLMResponse(BaseModel):
    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    tokens_used: int = 0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchRequest(BaseModel):
    query: str
    k: int = Field(5, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    include_content: bool = Field(False, description="Return full chunk content")
    snippet_len: int = Field(240, ge=50, le=2000, description="Snippet length when include_content=false")
    include_metadata: bool = Field(True, description="Return metadata in results")
    evidence_max_total: int = Field(50, ge=1, le=500, description="Max evidence items after hybrid policy")
    evidence_max_chunks: Optional[int] = Field(None, ge=0, le=200, description="Optional chunk evidence budget")
    evidence_max_memory: Optional[int] = Field(None, ge=0, le=200, description="Optional memory evidence budget")
    evidence_max_edges: Optional[int] = Field(None, ge=0, le=200, description="Optional edge evidence budget")
    evidence_dedupe: bool = Field(True, description="Enable evidence deduplication by type/id")
    evidence_rerank: bool = Field(True, description="Enable deterministic evidence reranking")

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    snippet: str
    content: Optional[str] = None
    source_document: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HybridSearchResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)
    graph: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)

class ExportRequest(BaseModel):
    document_id: Optional[str] = None
    content: Optional[str] = None
    format: str = Field("pdf")
    options: Optional[Dict[str, Any]] = None

class ExportResult(BaseModel):
    format: str
    output_path: Optional[str] = None
    bytes_base64: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: str
    services: Dict[str, Any]

class DocumentOut(BaseModel):
    id: str
    filename: str
    size_bytes: int = 0
    status: str = "unknown"
    workspace_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentDetailOut(BaseModel):
    id: str
    filename: str
    size_bytes: int = 0
    mime: Optional[str] = None
    status: str = "unknown"
    workspace_id: str = "default"
    chunks_count: Optional[int] = None
    indexed_at: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnswerConfirmRequest(BaseModel):
    query: str = Field(min_length=1)
    decision: Literal["approve", "cancel"] = Field(
        description="Handshake decision for confirmation workflow"
    )
    confirmation_token: str = Field(min_length=1)
    action_ids: List[str] = Field(default_factory=list)
    session_id: str = Field(default="default", min_length=1, max_length=128)
    filters: Dict[str, Any] = Field(default_factory=dict)

