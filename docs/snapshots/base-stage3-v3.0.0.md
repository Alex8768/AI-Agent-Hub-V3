# base-stage3-v3.0.0

**Tag:** `base-stage3-v3.0.0`  
**Date:** 2026-02-24  
**Status:** Stable Base (Stage 3)

---

## 🎯 Summary

Stable cross-platform Base release with:

- Hosted CI (Linux/Windows CPU)
- Self-hosted Win RTX (CUDA)
- Self-hosted Mac M4 (MPS)
- Clean install scripts (Win/Linux)
- Extras-based dependency profiles
- Atomic FAISS persistence (Windows-safe)
- Non-blocking vector operations
- Graceful shutdown
- JWT auth + Workspace isolation
- Torch optionality (safe fallback)
- All unit + install tests passing

---

## ✅ Platforms validated

| Platform | Mode | Status |
|----------|------|--------|
| Linux | CPU | ✅ CI green |
| Windows 10 | CPU | ✅ CI green |
| Windows RTX 4050 | CUDA | ✅ Self-hosted green |
| Mac M4 | MPS | ✅ Self-hosted green |

---

## 📦 Installation profiles

- `[base]`
- `[base,security]`
- `[base,security,embeddings,faiss,ingest]`
- `[... ,test]` for CI

Clean install verified via:
- `scripts/test_install.sh`
- `scripts/test_install.ps1`

---

## 🔒 Stability guarantees

- No event loop blocking in FAISS
- Atomic index save (temp + replace)
- Workspace path protection
- Device resolution unified via accelerator
- Deterministic startup/shutdown lifecycle

---

## 🚀 Next Phase

Pro Layer:
- Qdrant store
- Roles / ACL
- Memory layer
- GraphRAG vertical

---

Base layer is considered production-ready for controlled environments.

