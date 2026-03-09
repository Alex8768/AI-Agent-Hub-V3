from __future__ import annotations

from typing import TypedDict


class OCRSourceRef(TypedDict):
    document_id: str
    page_index: int
    block_index: int
    mime_type: str
    uri: str


class OCRTextBlock(TypedDict):
    text: str
    confidence: float
    bbox: list[float]
    source_ref: OCRSourceRef


class OCRPageExtraction(TypedDict):
    page_index: int
    text: str
    confidence: float
    blocks: list[OCRTextBlock]
    source_refs: list[OCRSourceRef]


class OCRExtractionResult(TypedDict):
    provider: str
    document_id: str
    total_pages: int
    pages: list[OCRPageExtraction]
    combined_text: str
    average_confidence: float
    warnings: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_int(value: object, *, default: int = 0, min_value: int = 0, max_value: int = 1_000_000) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            rows.append(item)
    return sorted(set(rows))


def _normalize_bbox(values: object) -> list[float]:
    raw = list(values or [])
    if len(raw) != 4:
        return []
    return [_normalize_float_01(item, default=0.0) for item in raw]


def build_ocr_source_ref(
    *,
    document_id: object,
    page_index: object,
    block_index: object = 0,
    mime_type: object = "",
    uri: object = "",
) -> OCRSourceRef:
    return {
        "document_id": _normalize_string(document_id),
        "page_index": _normalize_int(page_index, default=0, min_value=0),
        "block_index": _normalize_int(block_index, default=0, min_value=0),
        "mime_type": _normalize_string(mime_type),
        "uri": _normalize_string(uri),
    }


def build_ocr_text_block(
    *,
    text: object,
    confidence: object,
    bbox: object = None,
    source_ref: dict[str, object] | OCRSourceRef | None = None,
) -> OCRTextBlock:
    source = build_ocr_source_ref(
        document_id=(dict(source_ref or {}).get("document_id", "")),
        page_index=(dict(source_ref or {}).get("page_index", 0)),
        block_index=(dict(source_ref or {}).get("block_index", 0)),
        mime_type=(dict(source_ref or {}).get("mime_type", "")),
        uri=(dict(source_ref or {}).get("uri", "")),
    )
    return {
        "text": _normalize_string(text),
        "confidence": _normalize_float_01(confidence, default=0.0),
        "bbox": _normalize_bbox(bbox),
        "source_ref": source,
    }


def build_ocr_page_extraction(
    *,
    page_index: object,
    text: object,
    confidence: object,
    blocks: object = None,
    source_refs: object = None,
) -> OCRPageExtraction:
    normalized_blocks: list[OCRTextBlock] = []
    for raw in list(blocks or []):
        row = dict(raw or {})
        normalized_blocks.append(
            build_ocr_text_block(
                text=row.get("text", ""),
                confidence=row.get("confidence", 0.0),
                bbox=row.get("bbox", []),
                source_ref=row.get("source_ref", {}),
            )
        )
    normalized_blocks.sort(
        key=lambda x: (
            int(dict(x.get("source_ref") or {}).get("block_index", 0) or 0),
            str(x.get("text", "") or ""),
        )
    )

    normalized_source_refs: list[OCRSourceRef] = []
    for raw in list(source_refs or []):
        row = dict(raw or {})
        normalized_source_refs.append(
            build_ocr_source_ref(
                document_id=row.get("document_id", ""),
                page_index=row.get("page_index", page_index),
                block_index=row.get("block_index", 0),
                mime_type=row.get("mime_type", ""),
                uri=row.get("uri", ""),
            )
        )
    normalized_source_refs.sort(
        key=lambda x: (
            int(x.get("page_index", 0) or 0),
            int(x.get("block_index", 0) or 0),
            str(x.get("uri", "") or ""),
        )
    )
    return {
        "page_index": _normalize_int(page_index, default=0, min_value=0),
        "text": _normalize_string(text),
        "confidence": _normalize_float_01(confidence, default=0.0),
        "blocks": normalized_blocks,
        "source_refs": normalized_source_refs,
    }


def build_ocr_extraction_result(
    *,
    provider: object,
    document_id: object,
    pages: object,
    warnings: object = None,
) -> OCRExtractionResult:
    normalized_pages: list[OCRPageExtraction] = []
    for raw in list(pages or []):
        row = dict(raw or {})
        normalized_pages.append(
            build_ocr_page_extraction(
                page_index=row.get("page_index", 0),
                text=row.get("text", ""),
                confidence=row.get("confidence", 0.0),
                blocks=row.get("blocks", []),
                source_refs=row.get("source_refs", []),
            )
        )
    normalized_pages.sort(key=lambda x: int(x.get("page_index", 0) or 0))

    lines = [str(page.get("text", "") or "") for page in normalized_pages]
    lines = [line for line in lines if line]
    confidence_values = [float(page.get("confidence", 0.0) or 0.0) for page in normalized_pages]
    average_confidence = (
        float(sum(confidence_values) / len(confidence_values))
        if confidence_values
        else 0.0
    )
    return {
        "provider": _normalize_string(provider),
        "document_id": _normalize_string(document_id),
        "total_pages": int(len(normalized_pages)),
        "pages": normalized_pages,
        "combined_text": "\n\n".join(lines),
        "average_confidence": _normalize_float_01(average_confidence, default=0.0),
        "warnings": _normalize_string_list(warnings),
    }


def build_ocr_extraction_result_from_payload(
    *,
    payload: dict[str, object] | None,
    provider: object,
    document_id: object,
) -> OCRExtractionResult:
    raw = payload if isinstance(payload, dict) else {}
    return build_ocr_extraction_result(
        provider=provider,
        document_id=document_id,
        pages=raw.get("pages", []),
        warnings=raw.get("warnings", []),
    )
