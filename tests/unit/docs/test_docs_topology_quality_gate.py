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


def test_docs_topology_quality_gate_root_stubs_point_to_canonical():
    cases = {
        "PROJECT_ANCHOR.md": "docs/development/PROJECT_ANCHOR.md",
        "STATUS.md": "docs/development/STATUS.md",
        "PROJECT_CHECKLIST.md": "docs/development/PROJECT_CHECKLIST.md",
        "PLATFORM_FEATURES.md": "docs/architecture/PLATFORM_FEATURES.md",
    }
    for root_file, target in cases.items():
        content = _read(root_file)
        assert "Compatibility Stub" in content
        assert f"`{target}`" in content


def test_docs_topology_quality_gate_canonical_content_markers():
    assert "## Active Anchor" in _read("docs/development/PROJECT_ANCHOR.md")
    assert "## Current Active Anchor" in _read("docs/development/STATUS.md")
    assert "## Current Work — A2.32 Docs Topology Cleanup" in _read(
        "docs/development/PROJECT_CHECKLIST.md"
    )
    assert "## Capability Map" in _read("docs/architecture/PLATFORM_FEATURES.md")
