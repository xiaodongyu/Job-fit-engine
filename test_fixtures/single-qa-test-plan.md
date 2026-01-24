# Single QA Test Plan

Smoke / sanity QA of the backend pipeline using only the three fixtures in `test_fixtures/`: **`resume.txt`**, **`jd.txt`**, and **`materials.txt`**. No manifests, benchmark resumes, or JD PDFs.

**Scope:** Upload (resume + materials merged) → poll until ready → cluster experience → match-by-cluster with JD text. Optionally analyze/fit.

---

## Prerequisites

- **Backend** running at `http://localhost:8000` (e.g. `uvicorn main:app --reload --port 8000` from `backend/`).
- **`GEMINI_API_KEY`** set in `backend/.env`.
- The three files exist: `test_fixtures/resume.txt`, `test_fixtures/jd.txt`, `test_fixtures/materials.txt`.

All commands below are run from the **project root**. Use a fixed `session_id` (`single_qa_test`) for reproducibility.

---

## Step 1: Health check

```bash
curl -sf http://localhost:8000/health
```

**Pass:** HTTP 200, JSON `{"status":"ok",...}`. **Fail:** Non-200 or connection refused.

---

## Step 2: Upload (resume + materials merged)

Merge `resume.txt` and `materials.txt`, then `POST /resume/upload/json` with `session_id` and `text`.

**With jq:**

```bash
SESSION_ID="single_qa_test"
curl -s -X POST http://localhost:8000/resume/upload/json \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg sid "$SESSION_ID" \
    --rawfile text <(cat test_fixtures/resume.txt test_fixtures/materials.txt) \
    '{ session_id: $sid, text: $text }')"
```

**Without jq (Python):**

```bash
SESSION_ID="single_qa_test"
curl -s -X POST http://localhost:8000/resume/upload/json \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
with open('test_fixtures/resume.txt') as f:
    r = f.read()
with open('test_fixtures/materials.txt') as f:
    m = f.read()
print(json.dumps({'session_id': '$SESSION_ID', 'text': r + m}))
")"
```

Save `session_id` and `upload_id` from the response. Example: `{"session_id":"single_qa_test","upload_id":"abc123..."}`.

**Pass:** Response contains `session_id` and `upload_id`. **Fail:** 4xx/5xx or missing fields.

---

## Step 3: Poll until ready

```bash
UPLOAD_ID="<paste upload_id from step 2>"
curl -s "http://localhost:8000/resume/status?upload_id=$UPLOAD_ID"
```

Repeat until `"status": "ready"` (or `"error"` → fail). Typical sequence: `uploading` → `parsing` → `chunking` → `embedding` → `indexing` → `ready`.

**Pass:** `status` becomes `ready`. **Fail:** `status` is `error` (check `detail`) or timeout.

---

## Step 4: Cluster experience

```bash
SESSION_ID="single_qa_test"
curl -s -X POST http://localhost:8000/experience/cluster \
  -H "Content-Type: application/json" \
  -d '{"session_id":"'"$SESSION_ID"'","items":[],"resume_text":null}'
```

**Pass:** Response includes `clusters` (non-empty) with MLE/DS/SWE/QR/QD and evidence. **Fail:** 4xx/5xx or empty `clusters`.

---

## Step 5: Match by cluster (JD from `jd.txt`)

```bash
SESSION_ID="single_qa_test"
curl -s -X POST http://localhost:8000/analyze/match-by-cluster \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
with open('test_fixtures/jd.txt') as f:
    jd = f.read()
print(json.dumps({
    'session_id': '$SESSION_ID',
    'use_curated_jd': False,
    'jd_text': jd
}))
")"
```

**With jq:** use `jq -n --arg sid "$SESSION_ID" --rawfile jd test_fixtures/jd.txt '{ session_id: $sid, use_curated_jd: false, jd_text: $jd }'` in place of the Python snippet.

**Pass:** Response includes `cluster_matches` and `overall_match_pct`. **Fail:** 4xx/5xx or missing fields.

---

## Step 6 (optional): Analyze fit

Same `session_id` and `jd_text` from `jd.txt`, plus `target_role` (e.g. `SWE`):

```bash
SESSION_ID="single_qa_test"
curl -s -X POST http://localhost:8000/analyze/fit \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
with open('test_fixtures/jd.txt') as f:
    jd = f.read()
print(json.dumps({
    'session_id': '$SESSION_ID',
    'target_role': 'SWE',
    'use_curated_jd': False,
    'jd_text': jd
}))
")"
```

**Pass:** 200 with `recommended_roles`, `requirements`, `gap`, `evidence`. **Fail:** 4xx/5xx.

---

## Pass/fail summary

| Check | Pass | Fail |
|-------|------|------|
| Step 1 | Health 200 | Non-200 or unreachable |
| Step 2 | `session_id` + `upload_id` in response | Upload error or missing |
| Step 3 | Poll reaches `ready` | `error` or timeout |
| Step 4 | `clusters` non-empty | Error or empty clusters |
| Step 5 | `cluster_matches` + `overall_match_pct` present | Error or missing |
| Step 6 (optional) | 200 with fit payload | 4xx/5xx |

**Overall pass:** All of steps 1–5 pass. Step 6 is optional.

---

## See also

For the **upload + poll + analyze/fit** subset only (no cluster, no match-by-cluster), you can use the existing script with the same fixtures:

```bash
./scripts/test-offline.sh -r test_fixtures/resume.txt -j test_fixtures/jd.txt -m test_fixtures/materials.txt
```

The full single plan above (steps 1–5, optional 6) remains curl-based and includes cluster + match-by-cluster.
