from __future__ import annotations

from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class SourceRef(BaseModel):
    document_id: str
    chunk_id: str
    snippet: str = Field(..., max_length=240)


class ExtractedEntity(BaseModel):
    node_type: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=512)
    aliases: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_ref: SourceRef


class ExtractedRelation(BaseModel):
    rel_type: str = Field(..., min_length=1, max_length=64)
    src_name: str = Field(..., min_length=1, max_length=512)
    src_type: str = Field(..., min_length=1, max_length=64)
    dst_name: str = Field(..., min_length=1, max_length=512)
    dst_type: str = Field(..., min_length=1, max_length=64)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_ref: SourceRef


class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relations: List[ExtractedRelation] = Field(default_factory=list)
    notes: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    @field_validator("entities", "relations")
    @classmethod
    def _cap_sizes(cls, v):
        # Hard caps to avoid runaway outputs (UI & DB safety)
        if len(v) > 64:
            return v[:64]
        return v
