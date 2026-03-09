from __future__ import annotations

from src.services.document.ingest_service import IngestService
from src.services.document.ocr import (
    build_ocr_extraction_result,
    build_ocr_quality_summary,
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


class _VectorStoreStub:
    name = "vector-stub"

    def __init__(self) -> None:
        self.documents = []

    async def add_documents(self, *, documents, embeddings):
        _ = embeddings
        self.documents.extend(list(documents or []))
        return [doc.id for doc in list(documents or [])]

    async def get_stats(self):
        return {"ntotal": len(self.documents)}

    async def health_check(self):
        return {"status": "healthy"}


def test_ocr_quality_gate_contracts_are_deterministic():
    extraction_a = build_ocr_extraction_result(
        provider="tesseract",
        document_id="doc-1",
        pages=[{"page_index": 0, "text": "x", "confidence": 0.9}],
        warnings=[],
    )
    extraction_b = build_ocr_extraction_result(
        provider="tesseract",
        document_id="doc-1",
        pages=[{"page_index": 0, "text": "x", "confidence": 0.9}],
        warnings=[],
    )
    assert extraction_a == extraction_b

    quality_a = build_ocr_quality_summary(
        extraction_result=extraction_a,
        min_confidence=0.7,
        min_coverage=0.8,
    )
    quality_b = build_ocr_quality_summary(
        extraction_result=extraction_b,
        min_confidence=0.7,
        min_coverage=0.8,
    )
    assert quality_a == quality_b


async def test_ocr_quality_gate_runtime_provider_parity():
    provider = _StaticProvider(
        payload={
            "pages": [
                {"page_index": 0, "text": "ocr text", "confidence": 0.95},
                {"page_index": 1, "text": "", "confidence": 0.4},
            ],
            "warnings": [],
        },
        name="runtime_provider",
    )
    outcome = await run_ocr_provider(
        provider=provider,
        document_id="doc-rt",
        content_bytes=b"img-bytes",
        mime_type="image/png",
    )
    quality_direct = build_ocr_quality_summary(
        extraction_result=dict(outcome.get("result", {}) or {}),
        min_confidence=0.6,
        min_coverage=0.5,
    )

    service = IngestService(
        vector_store=_VectorStoreStub(),
        ocr_provider=provider,
        ocr_min_confidence=0.6,
        ocr_min_coverage=0.5,
        chunk_size=100,
        chunk_overlap=20,
    )
    text_after, ocr_diag = await service._maybe_apply_ocr_boundary(
        text="fallback",
        filename="scan.png",
        format=service._detect_format("scan.png"),
        document_id="doc-rt",
        source_bytes=b"img-bytes",
        mime_type="image/png",
    )
    assert text_after == "ocr text"
    assert dict(ocr_diag.get("quality") or {}) == quality_direct


async def test_ocr_quality_gate_low_quality_triggers_warn_path():
    provider = _StaticProvider(
        payload={"pages": [{"page_index": 0, "text": "", "confidence": 0.1}], "warnings": ["blurred_scan"]},
        name="low_quality_provider",
    )
    service = IngestService(
        vector_store=_VectorStoreStub(),
        ocr_provider=provider,
        ocr_min_confidence=0.8,
        ocr_min_coverage=0.9,
        chunk_size=100,
        chunk_overlap=20,
    )
    _, ocr_diag = await service._maybe_apply_ocr_boundary(
        text="fallback text",
        filename="scan.png",
        format=service._detect_format("scan.png"),
        document_id="doc-low",
        source_bytes=b"img-bytes",
        mime_type="image/png",
    )
    quality = dict(ocr_diag.get("quality") or {})
    assert quality.get("status") == "warn"
    assert "confidence_below_threshold" in list(quality.get("reason_codes") or [])
    assert "coverage_below_threshold" in list(quality.get("reason_codes") or [])
    assert "blurred_scan" in list(quality.get("warnings") or [])
