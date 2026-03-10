from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_approval_execution_gateway_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/APPROVAL_EXECUTION_GATEWAY_RUNTIME.md")
    required_markers = [
        "Approval session contract version: `v1`",
        "Execution idempotency contract version: `v1`",
        "Execution gateway contract version: `v1`",
        "`assistant_approval_session`",
        "`execution_idempotency`",
        "`assistant_execution_gateway`",
        "`POST /api/v1/answer/confirm`",
        "`idempotency_key`",
        "`handshake_idempotency_key`",
        "`safe_mode`",
        "`ready_for_execution`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing approval gateway runtime marker: {marker}"


def test_approval_execution_gateway_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/APPROVAL_EXECUTION_GATEWAY_RUNTIME.md" in readme
    assert "Approval execution gateway runtime docs quality gate" in roadmap
