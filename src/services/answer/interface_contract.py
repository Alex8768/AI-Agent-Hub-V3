from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request


@dataclass(slots=True)
class AnswerServiceRequestContract:
    http: Request
    req: object
    workspace_id: str
    engine: object | None = None
    retriever: object | None = None


def build_answer_service_request_contract(
    *,
    http: Request,
    req: object,
    workspace_id: str,
    engine: object | None = None,
    retriever: object | None = None,
) -> AnswerServiceRequestContract:
    return AnswerServiceRequestContract(
        http=http,
        req=req,
        workspace_id=str(workspace_id or ""),
        engine=engine,
        retriever=retriever,
    )
