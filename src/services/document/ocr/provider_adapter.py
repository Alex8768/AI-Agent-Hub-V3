from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict

from src.services.document.ocr.ocr_contract import (
    OCRExtractionResult,
    build_ocr_extraction_result_from_payload,
)


class OCRProviderError(TypedDict):
    code: str
    message: str
    retryable: bool


class OCRProviderOutcome(TypedDict):
    provider: str
    ok: bool
    result: OCRExtractionResult
    error: OCRProviderError | None


class OCRProvider(Protocol):
    name: str

    async def extract(
        self,
        *,
        document_id: str,
        content_bytes: bytes,
        mime_type: str,
    ) -> dict[str, object]:
        ...


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _build_error(*, code: object, message: object, retryable: object = False) -> OCRProviderError:
    normalized_code = _normalize_string(code).lower() or "ocr_provider_error"
    return {
        "code": normalized_code,
        "message": _normalize_string(message),
        "retryable": bool(retryable),
    }


def build_ocr_provider_outcome(
    *,
    provider: object,
    document_id: object,
    payload: dict[str, object] | None = None,
    error: dict[str, object] | OCRProviderError | None = None,
) -> OCRProviderOutcome:
    normalized_provider = _normalize_string(provider) or "unknown"
    extraction_result = build_ocr_extraction_result_from_payload(
        payload=payload if isinstance(payload, dict) else {},
        provider=normalized_provider,
        document_id=document_id,
    )
    normalized_error: OCRProviderError | None
    if isinstance(error, dict):
        normalized_error = _build_error(
            code=error.get("code", "ocr_provider_error"),
            message=error.get("message", ""),
            retryable=error.get("retryable", False),
        )
    else:
        normalized_error = None
    return {
        "provider": normalized_provider,
        "ok": normalized_error is None,
        "result": extraction_result,
        "error": normalized_error,
    }


async def run_ocr_provider(
    *,
    provider: OCRProvider,
    document_id: str,
    content_bytes: bytes,
    mime_type: str,
) -> OCRProviderOutcome:
    try:
        payload = await provider.extract(
            document_id=str(document_id or ""),
            content_bytes=bytes(content_bytes or b""),
            mime_type=str(mime_type or ""),
        )
        return build_ocr_provider_outcome(
            provider=getattr(provider, "name", "unknown"),
            document_id=document_id,
            payload=payload if isinstance(payload, dict) else {},
            error=None,
        )
    except Exception as exc:
        return build_ocr_provider_outcome(
            provider=getattr(provider, "name", "unknown"),
            document_id=document_id,
            payload={"pages": [], "warnings": ["provider_error"]},
            error={
                "code": "provider_runtime_error",
                "message": str(exc),
                "retryable": False,
            },
        )


@dataclass(slots=True)
class NoopOCRProvider:
    """Best-effort OCR provider fallback with deterministic empty output."""

    name: str = "noop"

    async def extract(
        self,
        *,
        document_id: str,
        content_bytes: bytes,
        mime_type: str,
    ) -> dict[str, object]:
        _ = content_bytes
        return {
            "pages": [],
            "warnings": [f"noop_provider:{_normalize_string(mime_type)}:{_normalize_string(document_id)}"],
        }
