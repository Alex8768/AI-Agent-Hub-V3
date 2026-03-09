from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_docs_topology_quality_gate_canonical_files_exist():
    expected = [
        "docs/development/PROJECT_ANCHOR.md",
        "docs/development/STATUS.md",
        "docs/development/PROJECT_CHECKLIST.md",
        "docs/architecture/PLATFORM_FEATURES.md",
        "docs/development/DOCS_TOPOLOGY_POLICY.md",
    ]
    for rel in expected:
        assert (ROOT / rel).exists(), f"Missing canonical doc: {rel}"


def test_docs_topology_quality_gate_root_stubs_removed():
    legacy_roots = [
        "PROJECT_ANCHOR.md",
        "STATUS.md",
        "PROJECT_CHECKLIST.md",
        "PLATFORM_FEATURES.md",
    ]
    for rel in legacy_roots:
        assert not (ROOT / rel).exists(), f"Legacy root doc must be removed: {rel}"


def test_docs_topology_quality_gate_canonical_content_markers():
    assert "## Active Anchor" in _read("docs/development/PROJECT_ANCHOR.md")
    assert "## Current Active Anchor" in _read("docs/development/STATUS.md")
    assert "## Current Work —" in _read("docs/development/PROJECT_CHECKLIST.md")
    assert "## Capability Map" in _read("docs/architecture/PLATFORM_FEATURES.md")
