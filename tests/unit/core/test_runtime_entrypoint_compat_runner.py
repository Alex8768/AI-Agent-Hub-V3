from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_run_utf8_is_compatibility_wrapper_to_canonical_entrypoint():
    content = (ROOT / "run_utf8.py").read_text(encoding="utf-8")
    assert "src.api.main:app" in content
    assert "Compatibility runner" in content
    assert "FastAPI(" not in content
