from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    path: Path
    size_bytes: int


class LocalStorage:
    """
    Local filesystem storage for Base.
    Root: ./data/uploads
    """

    def __init__(self, root_dir: str | None = None):
        self.root = Path(root_dir or "./data/uploads")
        self.root.mkdir(parents=True, exist_ok=True)

    def save_upload(self, workspace_id: str, doc_id: str, filename: str, data: bytes) -> StoredObject:
        safe_ws = workspace_id or "default"
        dest_dir = self.root / safe_ws / doc_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / filename
        dest_path.write_bytes(data)

        storage_key = str(dest_path.relative_to(Path("./data")))
        return StoredObject(storage_key=storage_key, path=dest_path, size_bytes=len(data))

    def delete(self, storage_key: str) -> None:
        p = Path("./data") / storage_key
        if p.exists():
            p.unlink()
