from __future__ import annotations

from typing import Protocol, TypedDict

from src.layers.pro.anticipatory.scanner import OpportunityScanResult, OpportunityScanner


class WhisperExecutionReceipt(TypedDict):
    run_id: str
    status: str
    safe_mode: bool
    duration_ms: int
    suggestion_count: int
    reason_codes: list[str]
    warnings: list[str]


class WhisperRunResult(TypedDict):
    receipt: WhisperExecutionReceipt
    scan: OpportunityScanResult
    suggestions: list[dict[str, object]]


class SessionMemoryWriter(Protocol):
    def store(self, *, key: str, value: object) -> None:
        """Persist whisper artifacts into session memory."""


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def build_whisper_execution_receipt(
    *,
    run_id: object,
    status: object,
    safe_mode: object,
    duration_ms: object,
    suggestion_count: object,
    reason_codes: object = None,
    warnings: object = None,
) -> WhisperExecutionReceipt:
    normalized_status = _normalize_string(status).lower()
    if normalized_status not in {"completed", "skipped", "failed"}:
        normalized_status = "completed"
    return {
        "run_id": _normalize_string(run_id),
        "status": normalized_status,
        "safe_mode": bool(safe_mode),
        "duration_ms": max(0, _normalize_int(duration_ms)),
        "suggestion_count": max(0, _normalize_int(suggestion_count)),
        "reason_codes": sorted(set([_normalize_string(x) for x in list(reason_codes or []) if _normalize_string(x)])),
        "warnings": sorted(set([_normalize_string(x) for x in list(warnings or []) if _normalize_string(x)])),
    }


def _build_suggestions_from_scan(scan: OpportunityScanResult, *, limit: int) -> list[dict[str, object]]:
    rows = list(scan.get("signals") or [])
    ranked = sorted(rows, key=lambda x: float(dict(x).get("confidence", 0.0)), reverse=True)
    suggestions: list[dict[str, object]] = []
    for row in ranked[: max(0, int(limit))]:
        signal = dict(row or {})
        suggestions.append(
            {
                "suggestion_id": f"suggestion:{_normalize_string(signal.get('signal_id', ''))}",
                "type": _normalize_string(signal.get("category", "")).lower() or "follow_up",
                "confidence": float(signal.get("confidence", 0.0) or 0.0),
                "reason": _normalize_string(signal.get("rationale", "")),
                "trigger": _normalize_string(signal.get("trigger", "")),
            }
        )
    return suggestions


async def run_whisper_safe_mode(
    *,
    scanner: OpportunityScanner,
    context: object,
    session_memory: object = None,
    registry: object = None,
    safe_mode: bool = True,
    suggestion_limit: int = 3,
    session_writer: SessionMemoryWriter | None = None,
) -> WhisperRunResult:
    if not safe_mode:
        receipt = build_whisper_execution_receipt(
            run_id="whisper:disabled",
            status="skipped",
            safe_mode=False,
            duration_ms=0,
            suggestion_count=0,
            reason_codes=["safe_mode_disabled"],
            warnings=[],
        )
        return {
            "receipt": receipt,
            "scan": {
                "status": "idle",
                "opportunity_score": 0.0,
                "signals": [],
                "reason_codes": [],
                "warnings": [],
            },
            "suggestions": [],
        }

    scan = scanner.scan(
        context=context,
        session_memory=session_memory,
        registry=registry,
        min_confidence=0.6,
    )
    suggestions = _build_suggestions_from_scan(scan, limit=int(suggestion_limit))
    receipt = build_whisper_execution_receipt(
        run_id=f"whisper:{_normalize_string(context)[:24].lower().replace(' ', '_') or 'run'}",
        status="completed",
        safe_mode=True,
        duration_ms=1,
        suggestion_count=len(suggestions),
        reason_codes=list(scan.get("reason_codes") or []),
        warnings=list(scan.get("warnings") or []),
    )
    if session_writer is not None:
        session_writer.store(
            key="anticipatory_suggestions",
            value=[dict(x) for x in suggestions],
        )
    return {
        "receipt": receipt,
        "scan": dict(scan),
        "suggestions": [dict(x) for x in suggestions],
    }


class WhisperRunner:
    """Safe-mode anticipatory runner with deterministic outputs."""

    def __init__(self, *, scanner: OpportunityScanner | None = None, safe_mode: bool = True) -> None:
        self._scanner = scanner or OpportunityScanner()
        self._safe_mode = bool(safe_mode)

    async def run_in_background(
        self,
        *,
        context: object,
        session_memory: object = None,
        registry: object = None,
        suggestion_limit: int = 3,
        session_writer: SessionMemoryWriter | None = None,
    ) -> WhisperRunResult:
        return await run_whisper_safe_mode(
            scanner=self._scanner,
            context=context,
            session_memory=session_memory,
            registry=registry,
            safe_mode=self._safe_mode,
            suggestion_limit=suggestion_limit,
            session_writer=session_writer,
        )
