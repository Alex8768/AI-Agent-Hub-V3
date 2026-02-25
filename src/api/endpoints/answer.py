from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.core.config import get_settings
from src.core.providers import get_reasoning_engine
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse


router = APIRouter(prefix="/api/v1", tags=["reasoning"])


@router.post("/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest) -> AnswerResponse:
    """Graph-aware answer synthesis (Pro).

    Feature-gated:
      - feature_reasoning
      - feature_graphrag
    """
    s = get_settings()
    if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
        # Hide Pro API surface when disabled
        raise HTTPException(status_code=404, detail="Not Found")

    # Composition root (MVP):
    # - retriever/llm are injected from the outer layer later.
    # For now we fail-fast until proper DI wiring is added.
    raise HTTPException(status_code=501, detail="Reasoning endpoint DI not wired yet")
