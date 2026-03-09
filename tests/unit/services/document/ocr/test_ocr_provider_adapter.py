from __future__ import annotations

import pytest

from src.services.document.ocr.provider_adapter import (
    NoopOCRProvider,
    build_ocr_provider_outcome,
    run_ocr_provider,
)


class _StaticProvider:
    def __init__(self, *, payload: dict[str, object], name: str = "static"):
        self.name = name
        self._payload = payload

    async def extract(self, *, document_id: str, content_bytes: bytes, mime_type: str) -> dict[str, object]:
        _ = document_id
        _ = content_bytes
        _ = mime_type
        return dict(self._payload)


class _FailingProvider:
    name = "failing"

    async def extract(self, *, document_id: str, content_bytes: bytes, mime_type: str) -> dict[str, object]:
        _ = document_id
        _ = content_bytes
        _ = mime_type
        raise RuntimeError("provider unavailable")


def test_build_ocr_provider_outcome_normalizes_success():
    outcome = build_ocr_provider_outcome(
        provider=" tesseract ",
        document_id=" doc-1 ",
        payload={
            "pages": [
                {"page_index": 0, "text": "hello", "confidence": 0.8},
            ],
            "warnings": [" low_confidence ", "low_confidence"],
        },
    )
    assert outcome["provider"] == "tesseract"
    assert outcome["ok"] is True
    assert outcome["error"] is None
    assert outcome["result"]["document_id"] == "doc-1"
    assert outcome["result"]["total_pages"] == 1
    assert outcome["result"]["warnings"] == ["low_confidence"]


@pytest.mark.asyncio
async def test_run_ocr_provider_returns_normalized_outcome():
    provider = _StaticProvider(
        payload={"pages": [{"page_index": 0, "text": "x", "confidence": 1.0}], "warnings": []}
    )
    outcome = await run_ocr_provider(
        provider=provider,
        document_id="doc-a",
        content_bytes=b"bytes",
        mime_type="image/png",
    )
    assert outcome["ok"] is True
    assert outcome["provider"] == "static"
    assert outcome["result"]["combined_text"] == "x"
    assert outcome["error"] is None


@pytest.mark.asyncio
async def test_run_ocr_provider_captures_provider_runtime_error():
    outcome = await run_ocr_provider(
        provider=_FailingProvider(),
        document_id="doc-b",
        content_bytes=b"bytes",
        mime_type="application/pdf",
    )
    assert outcome["ok"] is False
    assert outcome["provider"] == "failing"
    assert outcome["result"]["total_pages"] == 0
    error = dict(outcome["error"] or {})
    assert error.get("code") == "provider_runtime_error"
    assert error.get("retryable") is False
    assert "provider unavailable" in str(error.get("message", ""))


@pytest.mark.asyncio
async def test_noop_ocr_provider_is_deterministic():
    provider = NoopOCRProvider()
    first = await provider.extract(document_id="doc-z", content_bytes=b"", mime_type="image/jpeg")
    second = await provider.extract(document_id="doc-z", content_bytes=b"ignored", mime_type="image/jpeg")
    assert first == second
    outcome = await run_ocr_provider(
        provider=provider,
        document_id="doc-z",
        content_bytes=b"",
        mime_type="image/jpeg",
    )
    assert outcome["ok"] is True
    assert outcome["result"]["warnings"] == ["noop_provider:image/jpeg:doc-z"]
