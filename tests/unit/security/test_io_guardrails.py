from __future__ import annotations

from pathlib import Path


def _collect_py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*.py") if p.is_file()]


def test_no_direct_open_in_endpoints_and_document_services():
    """
    Guardrail: prevent accidental direct filesystem access in API endpoints and document services.
    - We allow infrastructure/storage layers to use aiofiles/open safely.
    - Here we focus on the highest-risk places where guard may be bypassed accidentally.
    """
    roots = [
        Path("src/api/endpoints"),
        Path("src/services/document"),
    ]

    offenders: list[str] = []
    for r in roots:
        for f in _collect_py_files(r):
            txt = f.read_text(encoding="utf-8", errors="ignore")

            # Explicit allow marker for known-safe endpoints (e.g., health probes)
            if "IO_GUARD: allow" in txt:
                continue

            # Allow explicitly guarded operations (rare) by allowing WorkspaceGuard usage
            uses_guard = ("WorkspaceGuard" in txt) or (".safe_path" in txt) or (".safe_path_root" in txt)

            # Direct open is suspicious in endpoints/services unless guard is used.
            if "open(" in txt and not uses_guard:
                offenders.append(str(f))

            # Direct write_text/read_text are also suspicious unless guard is used.
            if (".write_text(" in txt or ".read_text(" in txt) and not uses_guard:
                offenders.append(str(f))

    offenders = sorted(set(offenders))
    assert not offenders, "Direct filesystem access detected (add WorkspaceGuard or move to storage layer):\n" + "\n".join(offenders)
