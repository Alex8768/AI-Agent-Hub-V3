"""Answer observability logging helpers extracted from answer service."""

from __future__ import annotations

from fastapi import Request

from src.adapters.logging_adapter import get_logger
from src.layers.pro.reasoning.contracts import AnswerRequest
from src.observability.request_context import get_request_id

_LOGGER = get_logger()


def log_observability(http: Request, *, workspace_id: str, req: AnswerRequest) -> None:
    try:
        from loguru import logger

        rid = get_request_id(http)
        logger.info(
            "answer.endpoint request_id={} workspace={} qlen={} k={} depth={}",
            rid,
            workspace_id,
            len(req.query or ""),
            int(req.k or 0),
            int(req.graph_depth or 0),
        )
    except Exception as exc:
        _LOGGER.warning(
            "Answer service soft-failure: request observability logging skipped",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_service_observability_log_soft_failure",
            },
        )
