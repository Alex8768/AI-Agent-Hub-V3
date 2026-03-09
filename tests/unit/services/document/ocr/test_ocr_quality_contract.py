from __future__ import annotations

import pytest

from src.services.document.ocr.ocr_contract import build_ocr_extraction_result
from src.services.document.ocr.quality_contract import (
    build_ocr_quality_summary,
    build_ocr_quality_summary_from_payload,
)


def test_ocr_quality_summary_passes_when_scores_meet_thresholds():
    extraction = build_ocr_extraction_result(
        provider="tesseract",
        document_id="doc-1",
        pages=[
            {"page_index": 0, "text": "hello", "confidence": 0.9},
            {"page_index": 1, "text": "world", "confidence": 0.8},
        ],
        warnings=[],
    )
    summary = build_ocr_quality_summary(
        extraction_result=extraction,
        min_confidence=0.7,
        min_coverage=0.9,
    )
    assert summary["status"] == "pass"
    assert summary["confidence_score"] == pytest.approx(0.85)
    assert summary["coverage_score"] == 1.0
    assert summary["reason_codes"] == []


def test_ocr_quality_summary_warns_when_quality_below_thresholds():
    extraction = build_ocr_extraction_result(
        provider="tesseract",
        document_id="doc-2",
        pages=[
            {"page_index": 0, "text": "", "confidence": 0.3},
            {"page_index": 1, "text": "ok", "confidence": 0.5},
        ],
        warnings=["provider_warning"],
    )
    summary = build_ocr_quality_summary(
        extraction_result=extraction,
        min_confidence=0.8,
        min_coverage=0.8,
    )
    assert summary["status"] == "warn"
    assert summary["recognized_pages"] == 1
    assert summary["total_pages"] == 2
    assert summary["reason_codes"] == [
        "confidence_below_threshold",
        "coverage_below_threshold",
    ]
    assert summary["warnings"] == [
        "confidence_below_threshold",
        "coverage_below_threshold",
        "provider_warning",
    ]


def test_ocr_quality_summary_from_payload_handles_empty_pages():
    summary = build_ocr_quality_summary_from_payload(
        payload={
            "provider": "noop",
            "document_id": "doc-3",
            "pages": [],
            "warnings": [],
        },
        min_confidence=0.6,
        min_coverage=0.7,
    )
    assert summary["status"] == "warn"
    assert summary["total_pages"] == 0
    assert summary["coverage_score"] == 0.0
    assert summary["reason_codes"] == [
        "confidence_below_threshold",
        "coverage_below_threshold",
        "no_pages_extracted",
    ]
