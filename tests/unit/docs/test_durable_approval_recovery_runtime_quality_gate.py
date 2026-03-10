from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_durable_approval_recovery_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/DURABLE_APPROVAL_RECOVERY_RUNTIME.md")
    required_markers = [
        "Durable approval session contract version: `v1`",
        "Idempotency record contract version: `v1`",
        "`assistant_durable_approval_session`",
        "`assistant_idempotency_record`",
        "`durable_approval_session_contract_version`",
        "`idempotency_record_contract_version`",
        "`session:<sid>:durable:approval_session_record`",
        "`session:<sid>:durable:idempotency_record:<idempotency_key>`",
        "`confirmation_token_expired`",
        "`confirmation_token_consumed`",
        "`idempotency_replay_recovered_from_durable`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing durable recovery runtime marker: {marker}"


def test_durable_approval_recovery_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/DURABLE_APPROVAL_RECOVERY_RUNTIME.md" in readme
    assert "Durable approval recovery runtime docs quality gate" in roadmap
