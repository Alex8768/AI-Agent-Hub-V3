# base-hardened-v3.0.0

Tag: base-hardened-v3.0.0
Date: 2026-02-20
Goal: Freeze a procurement-friendly Base Hardening snapshot (security + determinism + cross-platform data paths).

## What’s included

### P0.1 — Torch optionality
- No direct torch imports outside accelerator paths
- Sentence-transformers usage guarded with clear error if torch missing

### P0.2 — Device/config cleanup
- DEVICE=auto|cpu|cuda|mps unified through settings.device
- Removed legacy EMBEDDING_DEVICE usage

### P0.3 — Auth + workspace enforcement
- Mock auth removed in production
- HS256 JWT validation
- Workspace dependency wired into endpoints (no hardcoded workspace_id="default")

### P0.4 — Filesystem safety
- WorkspaceGuard implemented (traversal + symlink escape protection)
- LocalStorage hardened (no escape outside uploads root)
- MCP filesystem server fixed to use safe root path validation
- Unit tests added

### P0.5 — Cross-platform data paths
- App data rooted at settings.data_dir (default cross-platform)
- Removed hardcoded ./data paths from functional code

## What’s NOT included (next steps)

### P1 — Production quality
- FAISS atomic save (Windows-safe) + non-blocking IO/executor
- Graceful shutdown coverage
- Additional load/concurrency tests

### Stage 2 — Cross-platform packaging
- pyproject.toml extras profiles (cpu/cuda/faiss/qdrant)
- Clean install scripts (Win/Linux)
- CI test matrix (Win/Linux, CPU/CUDA)

### Pro Layer
- Qdrant store, roles/ACL, Memory/GraphRAG vertical

## Smoke verification

Run server:
  uvicorn src.api.main:app --host 127.0.0.1 --port 8000

Health check:
  curl -sS http://127.0.0.1:8000/health | head

Unit tests:
  pytest -q
  python -m compileall src

