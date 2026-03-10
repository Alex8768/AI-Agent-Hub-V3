#!/usr/bin/env python3
"""Compatibility runner delegating to the canonical API entrypoint.

Canonical runtime entrypoint is `src.api.main:app`.
This wrapper is intentionally retained for local compatibility only.
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - local runtime fallback
        print(f"Import error: {exc}")
        print("Install runtime deps first, for example: pip install -e '.[base,test]'")
        return 1

    print("Starting compatibility runner.")
    print("Canonical entrypoint: uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
