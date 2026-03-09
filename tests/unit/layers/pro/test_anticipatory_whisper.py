from __future__ import annotations

import pytest

from src.layers.pro.anticipatory.scanner import OpportunityScanner
from src.layers.pro.anticipatory.whisper import (
    WhisperRunner,
    build_whisper_execution_receipt,
    run_whisper_safe_mode,
)


class _SessionWriterStub:
    def __init__(self) -> None:
        self.rows: dict[str, object] = {}

    def store(self, *, key: str, value: object) -> None:
        self.rows[str(key)] = value


def test_build_whisper_execution_receipt_normalizes_fields() -> None:
    receipt = build_whisper_execution_receipt(
        run_id=" r1 ",
        status="COMPLETED",
        safe_mode=1,
        duration_ms="12",
        suggestion_count="2",
        reason_codes=["a", "a", " b "],
        warnings=["w", "w"],
    )
    assert receipt == {
        "run_id": "r1",
        "status": "completed",
        "safe_mode": True,
        "duration_ms": 12,
        "suggestion_count": 2,
        "reason_codes": ["a", "b"],
        "warnings": ["w"],
    }


@pytest.mark.asyncio
async def test_run_whisper_safe_mode_produces_deterministic_suggestions() -> None:
    scanner = OpportunityScanner()
    writer = _SessionWriterStub()
    run_a = await run_whisper_safe_mode(
        scanner=scanner,
        context="document next plan",
        session_memory="pending unresolved",
        registry={"enabled": True},
        safe_mode=True,
        suggestion_limit=3,
        session_writer=writer,
    )
    run_b = await run_whisper_safe_mode(
        scanner=scanner,
        context="document next plan",
        session_memory="pending unresolved",
        registry={"enabled": True},
        safe_mode=True,
        suggestion_limit=3,
    )
    assert run_a == run_b
    assert run_a["receipt"]["status"] == "completed"
    assert len(run_a["suggestions"]) <= 3
    assert "anticipatory_suggestions" in writer.rows


@pytest.mark.asyncio
async def test_whisper_runner_skips_when_safe_mode_disabled() -> None:
    runner = WhisperRunner(safe_mode=False)
    result = await runner.run_in_background(context="document")
    assert result["receipt"]["status"] == "skipped"
    assert result["receipt"]["reason_codes"] == ["safe_mode_disabled"]
    assert result["suggestions"] == []
