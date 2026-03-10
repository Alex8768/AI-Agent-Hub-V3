from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.config import get_settings
from src.api.dependencies import get_workspace
from src.api.dependencies_impl import get_hybrid_retriever, get_rag_engine
from src.api.schemas import AnswerConfirmRequest
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse

from src.services.answer.answer_service import AnswerService
from src.services.answer.interface_contract import build_answer_service_request_contract


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
    contract = build_answer_service_request_contract(
        http=http,
        req=req,
        workspace_id=workspace_id,
        engine=engine,
        retriever=retriever,
    )
    return await service.handle_contract(contract)


@router.post("/answer/confirm", response_model=AnswerResponse)
async def answer_confirm(
    http: Request,
    req: AnswerConfirmRequest,
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
    if not getattr(s, "feature_assistant_mode", False) or not getattr(s, "feature_assistant_actions", False):
        raise HTTPException(status_code=400, detail="Assistant confirmation flow is disabled")

    mapped = AnswerRequest(
        query=req.query,
        session_id=req.session_id,
        filters={
            **dict(req.filters or {}),
            "handshake_decision": str(req.decision),
            "handshake_confirmation_token": str(req.confirmation_token),
            "handshake_action_ids": list(req.action_ids or []),
            "handshake_idempotency_key": str(req.idempotency_key or ""),
        },
    )
    service = AnswerService()
    contract = build_answer_service_request_contract(
        http=http,
        req=mapped,
        workspace_id=workspace_id,
        engine=engine,
        retriever=retriever,
    )
    return await service.handle_contract(contract)
