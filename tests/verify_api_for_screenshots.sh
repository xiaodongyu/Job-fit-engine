#!/bin/bash
# 运行此脚本以获取作业截图所需的验证输出
# 使用前请确保：1) 后端已启动 (cd backend && uvicorn main:app --port 8000)
#              2) backend/.env 中已配置 GEMINI_API_KEY
#
# 用法: 在项目根目录运行
#   ./tests/verify_api_for_screenshots.sh
# 或
#   bash tests/verify_api_for_screenshots.sh

set -e
cd "$(dirname "$0")/.."
API_BASE="${API_BASE:-http://localhost:8000}"
RESUME_FILE="test_fixtures/resume_cross_functional_role/Resume_1_MLE_Enriched.txt"

echo "=============================================="
echo "截图 1: 后端健康检查"
echo "=============================================="
echo ""
echo "\$ curl $API_BASE/health"
echo ""
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""

echo "=============================================="
echo "截图 2: 上传简历"
echo "=============================================="
UPLOAD_JSON=$(python3 -c "
import json
text = open('$RESUME_FILE').read() if __import__('os').path.exists('$RESUME_FILE') else 'John Doe, Software Engineer. 5 years Python, AWS, ML. Skills: Python, TensorFlow, SQL.'
print(json.dumps({'text': text}))
")
echo ""
echo "\$ curl -X POST $API_BASE/resume/upload/json -H 'Content-Type: application/json' -d '{\"text\": \"...\"}'"
echo ""
UPLOAD_RESP=$(curl -s -X POST "$API_BASE/resume/upload/json" \
  -H "Content-Type: application/json" \
  -d "$UPLOAD_JSON")
echo "$UPLOAD_RESP" | python3 -m json.tool
SESSION_ID=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session_id',''))")
UPLOAD_ID=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('upload_id',''))")
echo ""

echo "等待简历处理完成..."
for i in {1..60}; do
  STATUS=$(curl -s "$API_BASE/resume/status?upload_id=$UPLOAD_ID" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
  if [ "$STATUS" = "ready" ]; then
    echo "状态: ready"
    break
  fi
  if [ "$STATUS" = "error" ]; then
    echo "状态: error - 处理失败"
    exit 1
  fi
  echo -n "."
  sleep 2
done
echo ""

echo "=============================================="
echo "截图 3: AI 功能验证 - POST /analyze/fit"
echo "=============================================="
echo ""
echo "$ curl -X POST $API_BASE/analyze/fit -H 'Content-Type: application/json' -d '{...}'"
echo ""
curl -s -X POST "$API_BASE/analyze/fit" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"target_role\": \"MLE\",
    \"use_curated_jd\": false,
    \"jd_text\": \"ML Engineer: Python, PyTorch, model deployment, MLOps, 5+ years.\"
  }" | python3 -m json.tool
echo ""

echo "=============================================="
echo "截图 4: AI 功能验证 - POST /resume/generate"
echo "=============================================="
echo ""
echo "$ curl -X POST $API_BASE/resume/generate -H 'Content-Type: application/json' -d '{...}'"
echo ""
curl -s -X POST "$API_BASE/resume/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"target_role\": \"MLE\",
    \"use_curated_jd\": false,
    \"jd_text\": \"ML Engineer: Python, PyTorch, model deployment.\"
  }" | python3 -m json.tool
echo ""
echo "验证完成。请对上述输出截图。"
