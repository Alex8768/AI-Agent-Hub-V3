from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_api_docs_quality_gate_contains_runtime_endpoint_markers():
    content = _read("docs/api/README.md")
    required_markers = [
        "`GET /api/v1/health/deep`",
        "`POST /api/v1/search-hybrid`",
        "`POST /api/v1/answer`",
        "`GET /api/v1/tools`",
        "`POST /api/v1/tools/{tool_name}/invoke`",
        "`GET /api/v1/export/{export_id}/download`",
        "`GET /api/v1/trace-test`",
        "`GET /api/v1/documents/{document_id}`",
        "`DELETE /api/v1/documents/{document_id}`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing API docs marker: {marker}"


def test_api_docs_quality_gate_contains_flag_defaults_and_gating_notes():
    content = _read("docs/api/README.md")
    required_markers = [
        "`feature_reasoning_api=false`",
        "`feature_reasoning=false`",
        "`feature_graphrag=false`",
        "`feature_hybrid_search_api=false`",
        "`streaming_enabled=false`",
        "`rate_limit_enabled=false`",
        "`POST /api/v1/answer` requires:",
        "`POST /api/v1/search-hybrid` requires:",
        "`/api/v1/tools*` endpoints require:",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing flag/gating docs marker: {marker}"


def test_api_docs_quality_gate_roadmap_flag_table_includes_default_off_markers():
    content = _read("docs/roadmaps/pro-v3.1.md")
    required_markers = [
        "feature_reasoning_api",
        "feature_hybrid_search_api",
        "feature_reasoning_llm_enabled",
        "feature_reasoning_llm_dry_run",
        "default OFF",
        "feature_graph_rag",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing roadmap feature flag marker: {marker}"
