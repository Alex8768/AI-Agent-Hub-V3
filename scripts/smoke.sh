#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API="${API:-$BASE_URL}"
TMP_DIR="${TMP_DIR:-/tmp/ai-agent-hub-smoke}"
DEEP_HEALTH="${DEEP_HEALTH:-0}"   # set 1 to run /api/v1/health/deep
STREAM_ONCE="${STREAM_ONCE:-1}"   # keep 1 for CI/test friendliness

mkdir -p "$TMP_DIR"

echo "== AI Agent Hub V3 :: Base RC Smoke =="
echo "BASE_URL=$BASE_URL"
echo

echo "0) Preflight: server reachable?"
CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o /dev/null -w "%{http_code}" "$API/health" || true)"
if [[ "$CODE" != "200" ]]; then
  echo "   ❌ Server not reachable or /health not 200 (HTTP $CODE)"
  echo "   Start it first: uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
  exit 1
fi
echo "   ✅ reachable"
echo

get_json_checked() {
  local url="$1"
  local tmp="$TMP_DIR/resp.bin"
  local code
  code="$(curl -sS --compressed -H "Accept-Encoding: identity" -o "$tmp" -w "%{http_code}" "$url" || true)"
  if [[ "$code" != "200" ]]; then
    echo "   ❌ GET $url failed (HTTP $code)"
    echo "   --- body ---"
    cat "$tmp" || true
    echo
    exit 1
  fi
  if [[ ! -s "$tmp" ]]; then
    echo "   ❌ GET $url returned empty body"
    echo "   Try manually: curl -v $url"
    exit 1
  fi
  cat "$tmp"
}

post_json() {
  local url="$1"
  local body="$2"
  curl -sS --compressed -H "Accept-Encoding: identity" -H "Content-Type: application/json" -d "$body" "$url"
}

# gzip-safe JSON helpers (accept plain JSON or gzipped bytes)
pyjson() { python3 scripts/jsonutil.py pretty; }

json_get() { local key="$1"; python3 scripts/jsonutil.py get "$key"; }

json_list_len() { python3 scripts/jsonutil.py len; }

echo "1) Health (light)"
CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o /dev/null -w "%{http_code}" "$API/health" || true)"
if [[ "$CODE" != "200" ]]; then
  echo "   ❌ /health failed (HTTP $CODE)"
  curl -sS --compressed "$API/health" || true
  exit 1
fi
echo "   ✅ /health OK"

echo "2) Health (deep, optional)"
if [[ "$DEEP_HEALTH" == "1" ]]; then
  CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o /dev/null -w "%{http_code}" "$API/api/v1/health/deep" || true)"
  if [[ "$CODE" != "200" ]]; then
    echo "   ❌ /api/v1/health/deep failed (HTTP $CODE)"
    curl -sS --compressed "$API/api/v1/health/deep" || true
    exit 1
  fi
  echo "   ✅ /api/v1/health/deep OK"
else
  echo "   ⏭️  skipped (set DEEP_HEALTH=1)"
fi

echo "3) Documents list"
DOCS_BEFORE="$(get_json_checked "$API/api/v1/documents" | json_list_len)"
echo "   docs before: $DOCS_BEFORE"

echo "4) Upload (idempotent / dedup)"
FILE_PATH="$TMP_DIR/smoke.txt"
echo "This is a smoke document about foxes and dogs." > "$FILE_PATH"

UPLOAD1="$(curl -sS --compressed -H "Accept-Encoding: identity" -F "file=@${FILE_PATH};type=text/plain" "$API/api/v1/documents/upload")"
DOC_ID1="$(printf "%s" "$UPLOAD1" | json_get "id")"
echo "   upload#1 id=$DOC_ID1"

UPLOAD2="$(curl -sS --compressed -H "Accept-Encoding: identity" -F "file=@${FILE_PATH};type=text/plain" "$API/api/v1/documents/upload")"
DOC_ID2="$(printf "%s" "$UPLOAD2" | json_get "id")"
echo "   upload#2 id=$DOC_ID2"

if [[ "$DOC_ID1" != "$DOC_ID2" ]]; then
  echo "   ❌ Dedup failed: ids differ"
  exit 1
fi
echo "   ✅ Dedup OK"

echo "5) Search (snippet mode)"
SEARCH1="$(post_json "$API/api/v1/search" '{"query":"foxes","k":3,"include_metadata":false}')"
COUNT1="$(printf "%s" "$SEARCH1" | json_list_len)"
echo "   results: $COUNT1"
if [[ "$COUNT1" -lt 1 ]]; then
  echo "   ❌ Search returned no results"
  echo "$SEARCH1" | pyjson
  exit 1
fi
echo "   ✅ Search OK (snippet)"

echo "6) Search (include_content=true)"
SEARCH2="$(post_json "$API/api/v1/search" '{"query":"foxes","k":1,"include_content":true,"include_metadata":false}')"
COUNT2="$(printf "%s" "$SEARCH2" | json_list_len)"
if [[ "$COUNT2" -lt 1 ]]; then
  echo "   ❌ Search include_content returned no results"
  echo "$SEARCH2" | pyjson
  exit 1
fi
echo "   ✅ Search OK (include_content)"

echo "7) Export (content -> pdf) + download"
EXPORT="$(post_json "$API/api/v1/export" '{"content":"Hello export world!","format":"pdf"}')"
EXPORT_ID="$(printf "%s" "$EXPORT" | python3 scripts/jsonutil.py export_id)"
if [[ -z "$EXPORT_ID" ]]; then
  echo "   ❌ Export did not return export_id"
  echo "$EXPORT" | pyjson
  exit 1
fi
echo "   export_id=$EXPORT_ID"

HTTP_CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o "$TMP_DIR/export.pdf" -w "%{http_code}" "$API/api/v1/export/${EXPORT_ID}/download")"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "   ❌ Export download failed: HTTP $HTTP_CODE"
  exit 1
fi
SIZE="$(wc -c < "$TMP_DIR/export.pdf" | tr -d ' ')"
echo "   downloaded bytes=$SIZE"
if [[ "$SIZE" -lt 500 ]]; then
  echo "   ❌ Export PDF too small (unexpected)"
  exit 1
fi
echo "   ✅ Export OK"

echo "8) Delete document (DB + storage + FAISS purge)"
DEL_CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o /dev/null -w "%{http_code}" -X DELETE "$API/api/v1/documents/${DOC_ID1}")"
if [[ "$DEL_CODE" != "200" ]]; then
  echo "   ❌ Delete failed: HTTP $DEL_CODE"
  exit 1
fi
echo "   ✅ Delete OK"

echo "9) Get-by-id after delete should 404"
GET_CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o /dev/null -w "%{http_code}" "$API/api/v1/documents/${DOC_ID1}")"
if [[ "$GET_CODE" != "404" ]]; then
  echo "   ❌ Expected 404 after delete, got HTTP $GET_CODE"
  exit 1
fi
echo "   ✅ Get-by-id 404 OK"

echo "10) Streaming (once mode)"
STREAM_CODE="$(curl -sS --compressed -H "Accept-Encoding: identity" -o "$TMP_DIR/stream.txt" -w "%{http_code}" "$API/api/v1/stream/test-session?once=${STREAM_ONCE}")"
echo "   stream http=$STREAM_CODE"
if [[ "$STREAM_CODE" == "200" ]]; then
  head -n 5 "$TMP_DIR/stream.txt" | sed 's/^/   | /'
  echo "   ✅ Streaming OK (once)"
elif [[ "$STREAM_CODE" == "400" ]]; then
  echo "   ⏭️  Streaming disabled (expected in Base)"
else
  echo "   ❌ Unexpected streaming HTTP $STREAM_CODE"
  exit 1
fi

DOCS_AFTER="$(get_json_checked "$API/api/v1/documents" | json_list_len)"
echo
echo "docs after: $DOCS_AFTER"
echo "✅ SMOKE PASSED"
