from __future__ import annotations

from typing import TypedDict

from src.services.document.ocr.ocr_contract import (
    OCRExtractionResult,
    build_ocr_extraction_result,
)


class OCRQualitySummary(TypedDict):
    provider: str
    document_id: str
    total_pages: int
    recognized_pages: int
    confidence_score: float
    coverage_score: float
    quality_score: float
    min_confidence: float
    min_coverage: float
    status: str
    reason_codes: list[str]
    warnings: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_ocr_quality_summary(
    *,
    extraction_result: OCRExtractionResult,
    min_confidence: object = 0.6,
    min_coverage: object = 0.7,
) -> OCRQualitySummary:
    normalized_result = build_ocr_extraction_result(
        provider=extraction_result.get("provider", ""),
        document_id=extraction_result.get("document_id", ""),
        pages=extraction_result.get("pages", []),
        warnings=extraction_result.get("warnings", []),
    )
    normalized_min_confidence = _normalize_float_01(min_confidence, default=0.6)
    normalized_min_coverage = _normalize_float_01(min_coverage, default=0.7)
    pages = list(normalized_result.get("pages") or [])
    total_pages = int(len(pages))
    recognized_pages = int(sum(1 for page in pages if _normalize_string(page.get("text", ""))))
    confidence_score = _normalize_float_01(normalized_result.get("average_confidence", 0.0), default=0.0)
    coverage_score = (
        _normalize_float_01(float(recognized_pages) / float(total_pages), default=0.0)
        if total_pages > 0
        else 0.0
    )
    quality_score = _normalize_float_01((confidence_score * 0.6) + (coverage_score * 0.4), default=0.0)

    reasons: list[str] = []
    if total_pages <= 0:
        reasons.append("no_pages_extracted")
    if confidence_score < normalized_min_confidence:
        reasons.append("confidence_below_threshold")
    if coverage_score < normalized_min_coverage:
        reasons.append("coverage_below_threshold")

    status = "pass" if not reasons else "warn"
    warning_rows = [*_normalize_string_list(normalized_result.get("warnings", []))]
    if reasons:
        warning_rows = sorted(set([*warning_rows, *reasons]))
    return {
        "provider": _normalize_string(normalized_result.get("provider", "")),
        "document_id": _normalize_string(normalized_result.get("document_id", "")),
        "total_pages": total_pages,
        "recognized_pages": recognized_pages,
        "confidence_score": confidence_score,
        "coverage_score": coverage_score,
        "quality_score": quality_score,
        "min_confidence": normalized_min_confidence,
        "min_coverage": normalized_min_coverage,
        "status": status,
        "reason_codes": _normalize_string_list(reasons),
        "warnings": warning_rows,
    }


def build_ocr_quality_summary_from_payload(
    *,
    payload: dict[str, object] | None,
    min_confidence: object = 0.6,
    min_coverage: object = 0.7,
) -> OCRQualitySummary:
    row = payload if isinstance(payload, dict) else {}
    extraction_result = build_ocr_extraction_result(
        provider=row.get("provider", ""),
        document_id=row.get("document_id", ""),
        pages=row.get("pages", []),
        warnings=row.get("warnings", []),
    )
    return build_ocr_quality_summary(
        extraction_result=extraction_result,
        min_confidence=min_confidence,
        min_coverage=min_coverage,
    )
