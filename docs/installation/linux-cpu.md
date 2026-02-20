# Linux (CPU) Installation — AI Agent Hub V3

## Prerequisites
- Ubuntu/Debian (or similar)
- Python 3.12+
- Git

## Install (minimal base)
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[base]"

## Install (Base Full: embeddings + FAISS + ingest + security)
python -m pip install -e ".[base,security,embeddings,faiss,ingest]"

## Run
uvicorn src.api.main:app --host 127.0.0.1 --port 8000

## Verify
curl -sS http://127.0.0.1:8000/health | head

## Clean install test (recommended)
./scripts/test_install.sh base
./scripts/test_install.sh base_full
