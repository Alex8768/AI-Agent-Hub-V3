# Linux (CUDA) Installation — AI Agent Hub V3

## Prerequisites
- NVIDIA GPU + driver
- CUDA Toolkit compatible with your PyTorch build
- Python 3.12+
- Git

## Install (Base + embeddings)
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel

python -m pip install -e ".[base,security,embeddings,ingest]"

## Vector store options
Option A (Base): FAISS CPU
python -m pip install -e ".[faiss]"

Option B (Production CUDA): Qdrant (recommended)
python -m pip install -e ".[qdrant]"

Option C (Advanced): faiss-gpu (Linux only)
- faiss-gpu wheels are platform-specific.
- If you have a working faiss-gpu build, install it manually or add a dedicated extra later.

## Run + verify
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
curl -sS http://127.0.0.1:8000/health | head

## Clean install test
./scripts/test_install.sh base
./scripts/test_install.sh base_full
