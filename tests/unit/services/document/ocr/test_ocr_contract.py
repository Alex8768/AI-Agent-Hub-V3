from __future__ import annotations

from src.services.document.ocr.ocr_contract import (
    build_ocr_extraction_result,
    build_ocr_extraction_result_from_payload,
    build_ocr_page_extraction,
    build_ocr_source_ref,
    build_ocr_text_block,
)


def test_ocr_contract_builders_normalize_values():
    source_ref = build_ocr_source_ref(
        document_id=" doc-1 ",
        page_index="-1",
        block_index="4",
        mime_type=" image/png ",
        uri=" s3://doc/1 ",
    )
    assert source_ref == {
        "document_id": "doc-1",
        "page_index": 0,
        "block_index": 4,
        "mime_type": "image/png",
        "uri": "s3://doc/1",
    }

    block = build_ocr_text_block(
        text=" hello ",
        confidence="1.9",
        bbox=[-1, 0.2, 2, 0.7],
        source_ref=source_ref,
    )
    assert block["text"] == "hello"
    assert block["confidence"] == 1.0
    assert block["bbox"] == [0.0, 0.2, 1.0, 0.7]
    assert block["source_ref"] == source_ref


def test_ocr_extraction_result_is_deterministic_and_aggregated():
    result = build_ocr_extraction_result(
        provider="tesseract",
        document_id="doc-a",
        pages=[
            {
                "page_index": 1,
                "text": "Page 2",
                "confidence": 0.5,
                "blocks": [],
                "source_refs": [],
            },
            {
                "page_index": 0,
                "text": "Page 1",
                "confidence": 0.9,
                "blocks": [
                    {
                        "text": "b",
                        "confidence": 0.5,
                        "source_ref": {"document_id": "doc-a", "page_index": 0, "block_index": 2},
                    },
                    {
                        "text": "a",
                        "confidence": 0.5,
                        "source_ref": {"document_id": "doc-a", "page_index": 0, "block_index": 1},
                    },
                ],
                "source_refs": [{"document_id": "doc-a", "page_index": 0, "block_index": 1}],
            },
        ],
        warnings=[" low_confidence ", "low_confidence"],
    )
    assert result["total_pages"] == 2
    assert [page["page_index"] for page in result["pages"]] == [0, 1]
    assert result["combined_text"] == "Page 1\n\nPage 2"
    assert result["average_confidence"] == 0.7
    assert result["warnings"] == ["low_confidence"]
    assert [x["text"] for x in result["pages"][0]["blocks"]] == ["a", "b"]


def test_ocr_extraction_result_from_payload_defaults():
    result = build_ocr_extraction_result_from_payload(
        payload={"pages": [{"page_index": 0, "text": "ok", "confidence": 0.8}]},
        provider="tesseract",
        document_id="doc-z",
    )
    assert result["provider"] == "tesseract"
    assert result["document_id"] == "doc-z"
    assert result["total_pages"] == 1
    assert result["pages"][0] == build_ocr_page_extraction(
        page_index=0,
        text="ok",
        confidence=0.8,
        blocks=[],
        source_refs=[],
    )
