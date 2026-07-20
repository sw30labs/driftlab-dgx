#!/usr/bin/env bash
# Idempotent venv setup for driftlab-dgx on NVIDIA DGX Spark (Python 3.12 preferred).
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

VENV_DIR="${1:-.venv}"
PYTHON_BIN="${PYTHON:-${DRIFTLAB_PYTHON:-python3.12}}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "error: ${PYTHON_BIN} not found. Install Python 3.12 or set PYTHON=..." >&2
    exit 1
  fi
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "== creating ${VENV_DIR} with ${PYTHON_BIN} =="
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
pip install -e ".[llm,test]"

if [[ ! -f .env ]]; then
  echo "== creating .env from .env.example =="
  (umask 077; cp .env.example .env)
  chmod 600 .env
fi

echo "== pytest (no live LLM) =="
if ! python -m pytest -q; then
  echo
  echo "error: pytest failed. Fix tests before treating install as healthy." >&2
  exit 1
fi

echo
echo "Setup complete."
echo "  source ${VENV_DIR}/bin/activate"
echo "  ./driftlab doctor"
echo "  ./driftlab demo"
echo "  ./driftlab dashboard --port 8321"
echo "  # optional advisory narratives:"
echo "  #   ~/Desktop/start-vllm.sh nemotron-super"
echo "  #   set DRIFTLAB_LLM_PROVIDER=vllm in .env"
echo "  #   ./driftlab test-vllm"
