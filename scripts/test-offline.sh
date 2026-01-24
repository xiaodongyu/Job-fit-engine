#!/usr/bin/env bash
# Offline test: resume (PDF/TXT) + JD (TXT) + optional materials (TXT).
# Usage:
#   $0 --resume PATH --jd PATH [--materials PATH]
#   $0 -r PATH -j PATH [-m PATH]
# Backend must be running at BASE_URL (default http://localhost:8000).

set -e
BASE_URL="${BASE_URL:-http://localhost:8000}"
TARGET_ROLE="${TARGET_ROLE:-SWE}"
POLL_INTERVAL=2
MAX_WAIT=120

RESUME=""
JD=""
MATERIALS=""

usage() {
  echo "Usage: $0 --resume PATH --jd PATH [--materials PATH]"
  echo "       $0 -r PATH -j PATH [-m PATH]"
  echo ""
  echo "Options:"
  echo "  -r, --resume PATH    Resume (PDF or TXT)"
  echo "  -j, --jd PATH        Job description (plain text)"
  echo "  -m, --materials PATH Optional; merged with resume and uploaded as text."
  echo "                       If using PDF resume + materials, pdftotext required."
  echo ""
  echo "Env: BASE_URL ($BASE_URL), TARGET_ROLE ($TARGET_ROLE)"
  echo ""
  echo "Example:"
  echo "  $0 -r test_fixtures/resume.pdf -j test_fixtures/jd.txt"
  echo "  $0 --resume ./resume.pdf --jd ./jd.txt --materials ./notes.txt"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--resume)   RESUME="$2"; shift 2 ;;
    -j|--jd)       JD="$2"; shift 2 ;;
    -m|--materials) MATERIALS="$2"; shift 2 ;;
    -h|--help)     usage ;;
    *)             echo "Unknown option: $1"; usage ;;
  esac
done

[[ -n "$RESUME" && -n "$JD" ]] || usage

json_with_file() {
  local key="$1"
  local file="$2"
  if command -v jq &>/dev/null; then
    jq -n --arg sid "${SESSION_ID}" --rawfile val "$file" \
      "{ session_id: \$sid, target_role: \"$TARGET_ROLE\", use_curated_jd: false, ${key}: \$val }"
  else
    python3 -c "
import json, sys
with open('$file') as f:
    val = f.read()
print(json.dumps({
    'session_id': '${SESSION_ID}',
    'target_role': '$TARGET_ROLE',
    'use_curated_jd': False,
    '$key': val
}))
"
  fi
}

[[ -f "$RESUME" ]] || { echo "Resume not found: $RESUME"; exit 1; }
[[ -f "$JD" ]]    || { echo "JD file not found: $JD"; exit 1; }
[[ -z "$MATERIALS" ]] || [[ -f "$MATERIALS" ]] || { echo "Materials not found: $MATERIALS"; exit 1; }

echo "==> Health check $BASE_URL"
curl -sf "$BASE_URL/health" >/dev/null || { echo "Backend not reachable at $BASE_URL"; exit 1; }

echo "==> Upload resume"

if [[ -n "$MATERIALS" ]]; then
  # Merge resume + materials, upload as text
  if [[ "$RESUME" == *.pdf ]]; then
    if ! command -v pdftotext &>/dev/null; then
      echo "Materials provided with PDF resume: pdftotext required (poppler-utils)."
      echo "Install: sudo apt install poppler-utils   OR   use resume.txt + materials.txt"
      exit 1
    fi
    tmp=$(mktemp)
    trap "rm -f $tmp" EXIT
    pdftotext "$RESUME" - 2>/dev/null | cat - "$MATERIALS" > "$tmp"
    combined="$tmp"
  else
    tmp=$(mktemp)
    trap "rm -f $tmp" EXIT
    cat "$RESUME" "$MATERIALS" > "$tmp"
    combined="$tmp"
  fi
  if command -v jq &>/dev/null; then
    body=$(jq -n --rawfile text "$combined" '{ text: $text }')
  else
    body=$(python3 -c "import json; f=open('$combined'); print(json.dumps({'text': f.read()})); f.close()")
  fi
  out=$(curl -s -X POST "$BASE_URL/resume/upload/json" \
    -H "Content-Type: application/json" \
    -d "$body")
else
  # Upload as file (PDF) or text (TXT)
  if [[ "$RESUME" == *.pdf ]]; then
    out=$(curl -s -X POST "$BASE_URL/resume/upload" -F "file=@$RESUME")
  else
    if command -v jq &>/dev/null; then
      body=$(jq -n --rawfile text "$RESUME" '{ text: $text }')
    else
      body=$(python3 -c "import json; f=open('$RESUME'); print(json.dumps({'text': f.read()})); f.close()")
    fi
    out=$(curl -s -X POST "$BASE_URL/resume/upload/json" \
      -H "Content-Type: application/json" \
      -d "$body")
  fi
fi

SESSION_ID=$(echo "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('session_id',''))")
UPLOAD_ID=$(echo "$out"  | python3 -c "import json,sys; print(json.load(sys.stdin).get('upload_id',''))")
[[ -n "$SESSION_ID" && -n "$UPLOAD_ID" ]] || { echo "Upload failed: $out"; exit 1; }
echo "    session_id=$SESSION_ID upload_id=$UPLOAD_ID"

echo "==> Poll status until ready"
elapsed=0
while [[ $elapsed -lt $MAX_WAIT ]]; do
  st=$(curl -s "$BASE_URL/resume/status?upload_id=$UPLOAD_ID")
  status=$(echo "$st" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))")
  echo "    $status"
  [[ "$status" == "ready" ]] && break
  [[ "$status" == "error" ]] && { echo "    detail: $(echo "$st" | python3 -c "import json,sys; print(json.load(sys.stdin).get('detail',''))")"; exit 1; }
  sleep $POLL_INTERVAL
  elapsed=$((elapsed + POLL_INTERVAL))
done
[[ "$status" == "ready" ]] || { echo "Timeout waiting for ready"; exit 1; }

echo "==> Analyze fit (JD from $JD)"
body=$(json_with_file "jd_text" "$JD")
curl -s -X POST "$BASE_URL/analyze/fit" \
  -H "Content-Type: application/json" \
  -d "$body" | python3 -m json.tool

echo "==> Done"
