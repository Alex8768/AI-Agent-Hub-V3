import os
from pathlib import Path
import pytest

from src.security.workspace_guard import WorkspaceGuard, WorkspaceAccessError


def test_safe_path_blocks_traversal(tmp_path: Path):
    guard = WorkspaceGuard(base_dir=tmp_path)
    wid = "ws_test"
    root = guard.workspace_root(wid)
    root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(WorkspaceAccessError):
        guard.safe_path(wid, "../outside.txt")

    with pytest.raises(WorkspaceAccessError):
        guard.safe_path(wid, "../../etc/passwd")


def test_safe_path_blocks_absolute(tmp_path: Path):
    guard = WorkspaceGuard(base_dir=tmp_path)
    wid = "ws_test"
    guard.workspace_root(wid).mkdir(parents=True, exist_ok=True)

    abs_path = str(Path("/tmp/evil.txt"))
    with pytest.raises(WorkspaceAccessError):
        guard.safe_path(wid, abs_path)


def test_safe_path_allows_normal_relative(tmp_path: Path):
    guard = WorkspaceGuard(base_dir=tmp_path)
    wid = "ws_test"
    guard.workspace_root(wid).mkdir(parents=True, exist_ok=True)

    p = guard.safe_path(wid, "docs/file.txt")
    assert str(p).endswith(os.path.join("docs", "file.txt"))
    assert p.is_absolute()


def test_safe_path_blocks_symlink_escape(tmp_path: Path):
    # Skip on platforms that don't allow symlink creation without elevated perms
    guard = WorkspaceGuard(base_dir=tmp_path)
    wid = "ws_test"
    root = guard.workspace_root(wid)
    root.mkdir(parents=True, exist_ok=True)

    outside = tmp_path / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "secret.txt").write_text("secret", encoding="utf-8")

    link = root / "link_out"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except Exception:
        pytest.skip("Symlinks not supported or not permitted on this platform")

    with pytest.raises(WorkspaceAccessError):
        guard.safe_path(wid, "link_out/secret.txt")


def test_safe_path_root_blocks_traversal(tmp_path: Path):
    guard = WorkspaceGuard(base_dir=tmp_path)
    root = tmp_path / "root"
    root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(WorkspaceAccessError):
        guard.safe_path_root(root, "../outside.txt")

    with pytest.raises(WorkspaceAccessError):
        guard.safe_path_root(root, "../../etc/passwd")


def test_safe_path_root_allows_relative_inside(tmp_path: Path):
    guard = WorkspaceGuard(base_dir=tmp_path)
    root = tmp_path / "root"
    root.mkdir(parents=True, exist_ok=True)

    p = guard.safe_path_root(root, "a/b.txt")
    assert p.is_absolute()
    assert str(p).endswith("a/b.txt") or str(p).endswith("a\\b.txt")
