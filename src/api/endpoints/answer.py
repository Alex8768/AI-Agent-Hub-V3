from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.config import get_settings
from src.api.dependencies import get_workspace
from src.api.dependencies_impl import get_hybrid_retriever, get_rag_engine
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse

from src.services.answer.answer_service import AnswerService


router = APIRouter(prefix="/api/v1", tags=["reasoning"])



@router.post("/answer", response_model=AnswerResponse)
async def answer(
    http: Request,
    req: AnswerRequest,
    workspace_id: str = Depends(get_workspace),
    engine=Depends(get_rag_engine),
    retriever=Depends(get_hybrid_retriever),
) -> AnswerResponse:
    s = get_settings()
    if (
        not getattr(s, "feature_reasoning_api", False)
        or not getattr(s, "feature_reasoning", False)
        or not getattr(s, "feature_graphrag", False)
    ):
        raise HTTPException(status_code=404, detail="Not Found")

    service = AnswerService()
    return await service.handle(
        http,
        req,
        workspace_id=workspace_id,
        engine=engine,
        retriever=retriever,
    )
