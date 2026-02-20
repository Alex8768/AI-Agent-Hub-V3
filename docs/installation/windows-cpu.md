# Windows (CPU) Installation — AI Agent Hub V3

## Prerequisites
- Windows 10/11
- Python 3.12+ (3.12 recommended)
- Git
- (Optional) Visual C++ Build Tools if you hit build errors

## Install (minimal base)

From repo root:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[base]"

## Install (Base Full: embeddings + FAISS + ingest + security)

python -m pip install -e ".[base,security,embeddings,faiss,ingest]"

## Run

uvicorn src.api.main:app --host 127.0.0.1 --port 8000

## Verify

curl http://127.0.0.1:8000/health

## Clean install test (recommended)

.\scripts\test_install.ps1 -Profile base
.\scripts\test_install.ps1 -Profile base_full
