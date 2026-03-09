from __future__ import annotations

import pytest

from src.layers.pro.anticipatory.scanner import OpportunityScanner
from src.layers.pro.anticipatory.suggestions import build_proactive_suggestion_bundle
from src.layers.pro.anticipatory.whisper import run_whisper_safe_mode


class _SessionWriterStub:
    def __init__(self) -> None:
        self.rows: dict[str, object] = {}

    def store(self, *, key: str, value: object) -> None:
        self.rows[str(key)] = value


def _to_proactive_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        item = dict(row or {})
        out.append(
            {
                "suggestion_id": str(item.get("suggestion_id", "") or ""),
                "suggestion_type": str(item.get("type", "follow_up") or "follow_up"),
                "confidence": float(item.get("confidence", 0.0) or 0.0),
                "rationale": str(item.get("reason", "") or ""),
                "action_hint": str(item.get("trigger", "") or ""),
                "source_signal_id": str(item.get("suggestion_id", "") or "").replace("suggestion:", ""),
            }
        )
    return out


def test_anticipatory_quality_gate_scanner_and_bundle_deterministic() -> None:
    scanner = OpportunityScanner()
    scan_a = scanner.scan(
        context="review document and propose next plan",
        session_memory="pending follow-up",
        registry={"enabled": True},
    )
    scan_b = scanner.scan(
        context="review document and propose next plan",
        session_memory="pending follow-up",
        registry={"enabled": True},
    )
    assert scan_a == scan_b

    suggestions = [
        {
            "suggestion_id": "s1",
            "suggestion_type": "follow_up",
            "confidence": 0.7,
            "rationale": "r1",
            "action_hint": "h1",
            "source_signal_id": "x1",
        },
        {
            "suggestion_id": "s2",
            "suggestion_type": "automation",
            "confidence": 0.8,
            "rationale": "r2",
            "action_hint": "h2",
            "source_signal_id": "x2",
        },
    ]
    bundle_a = build_proactive_suggestion_bundle(suggestions=suggestions, limit=3)
    bundle_b = build_proactive_suggestion_bundle(suggestions=list(reversed(suggestions)), limit=3)
    assert bundle_a == bundle_b


@pytest.mark.asyncio
async def test_anticipatory_quality_gate_whisper_runtime_parity() -> None:
    scanner = OpportunityScanner()
    writer = _SessionWriterStub()
    run = await run_whisper_safe_mode(
        scanner=scanner,
        context="document next plan",
        session_memory="pending unresolved",
        registry={"enabled": True},
        safe_mode=True,
        suggestion_limit=3,
        session_writer=writer,
    )
    proactive_direct = build_proactive_suggestion_bundle(
        suggestions=_to_proactive_rows(list(run.get("suggestions") or [])),
        limit=3,
    )
    assert run["receipt"]["status"] == "completed"
    assert dict(run.get("scan") or {}).get("status") in {"active", "monitor", "idle"}
    assert dict(proactive_direct).get("top_suggestion_id", "") == str(
        (list(proactive_direct.get("suggestions") or [{}])[0] if proactive_direct.get("suggestions") else {}).get(
            "suggestion_id", ""
        )
    )
    assert "anticipatory_suggestions" in writer.rows


@pytest.mark.asyncio
async def test_anticipatory_quality_gate_safe_mode_disabled_path() -> None:
    run = await run_whisper_safe_mode(
        scanner=OpportunityScanner(),
        context="document",
        safe_mode=False,
    )
    assert run["receipt"]["status"] == "skipped"
    assert run["receipt"]["reason_codes"] == ["safe_mode_disabled"]
    assert run["suggestions"] == []
