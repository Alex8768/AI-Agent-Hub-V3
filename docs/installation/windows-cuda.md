# Windows (CUDA) Installation — AI Agent Hub V3

Note:
- CUDA is primarily targeted for Linux + NVIDIA in production.
- Windows CUDA setups vary; treat this as best-effort.

## Prerequisites
- NVIDIA GPU + recent driver
- CUDA Toolkit compatible with your PyTorch build
- Python 3.12+
- Git

## Install (Base + embeddings)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel

python -m pip install -e ".[base,security,embeddings,ingest]"

## Vector store
- FAISS GPU wheels are not guaranteed on Windows.
- Recommended production CUDA path: Linux + faiss-gpu or Qdrant.

FAISS CPU fallback:
python -m pip install -e ".[faiss]"

## Clean install test
.\scripts\test_install.ps1 -Profile base
.\scripts\test_install.ps1 -Profile base_full
