#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-base}"

echo "== AI Agent Hub V3 :: test_install.sh =="
echo "Profile: ${PROFILE}"

PYTHON_BIN="${PYTHON_BIN:-python3}"

WORKDIR="$(pwd)"
VENV_DIR="${WORKDIR}/.venv_test_install_${PROFILE}"

rm -rf "${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install -U pip setuptools wheel

if [[ "${PROFILE}" == "base" ]]; then
  python -m pip install -e ".[base]"
elif [[ "${PROFILE}" == "base_full" ]]; then
  python -m pip install -e ".[base,security,embeddings,faiss,ingest,test]"
else
  echo "Unknown profile: ${PROFILE}"
  exit 2
fi

python -m compileall src
pytest -q

echo "OK: install + compile + tests"
