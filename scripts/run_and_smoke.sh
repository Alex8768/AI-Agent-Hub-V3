#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-}"
# Pick a free local port if not provided
if [[ -z "${PORT}" ]]; then
  PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
fi

BASE_URL="${BASE_URL:-http://${HOST}:${PORT}}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-25}" # seconds

export BASE_URL

echo "== AI Agent Hub V3 :: Run + Smoke (Unix) =="
echo "BASE_URL=$BASE_URL"
echo

# Start uvicorn in background
uvicorn src.api.main:app --host "$HOST" --port "$PORT" >/tmp/ai-agent-hub-uvicorn.log 2>&1 &
PID="$!"
cleanup() {
  if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
    sleep 0.3
    kill -9 "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "1) Starting server (pid=$PID)"
# Wait for /health
deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
while true; do
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_URL/health" || true)"
  if [[ "$code" == "200" ]]; then
    echo "   ✅ /health is ready"
    break
  fi
  if [[ $(date +%s) -ge $deadline ]]; then
    echo "   ❌ Server did not become healthy within ${HEALTH_TIMEOUT}s (last HTTP=$code)"
    echo "   --- uvicorn log ---"
    tail -n 200 /tmp/ai-agent-hub-uvicorn.log || true
    exit 1
  fi
  sleep 0.35
done
echo

echo "2) Running smoke.sh"
./scripts/smoke.sh
echo
echo "✅ Run + Smoke PASSED"
