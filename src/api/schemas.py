from __future__ import annotations

from typing import Any, Dict, List, Optional
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


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


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


class Document(BaseModel):
    id: str
    filename: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: str
    services: Dict[str, str]

class DocumentOut(BaseModel):
    id: str
    filename: str
    size_bytes: int = 0
    status: str = "unknown"
    workspace_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)

