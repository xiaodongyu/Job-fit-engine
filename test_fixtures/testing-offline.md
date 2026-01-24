# Offline Testing with Local Files

You can test the backend using local files:

- **Resume PDF** – your resume
- **JD TXT** – job description as plain text
- **Additional materials TXT** – extra context (project notes, cover letter, etc.)

**Where to put them:** Use the **`test_fixtures/`** folder in the project root. Add your `resume.pdf` (or `resume.txt`) there; `jd.txt` and `materials.txt` samples are included. See [test_fixtures/README.md](../test_fixtures/README.md).

**Prerequisites:** Backend running (`uvicorn main:app --reload --port 8000` from `backend/`), `GEMINI_API_KEY` set in `backend/.env`. The backend needs network access to call Gemini; "offline" here means **no frontend** and **local files** as input.

---

## 1. Manual curl Commands

### Step 1: Upload resume (PDF)

```bash
cd /path/to/Job-fit-engine
curl -s -X POST http://localhost:8000/resume/upload \
  -F "file=@test_fixtures/resume.pdf"
```

Example response:

```json
{ "session_id": "a1b2c3d4", "upload_id": "xyz789abc" }
```

Save `session_id` and `upload_id` for the next steps.

### Step 2: Poll until processing is ready

```bash
curl -s "http://localhost:8000/resume/status?upload_id=YOUR_UPLOAD_ID"
```

Repeat until `"status": "ready"`. On error, `"status": "error"` and `"detail"` explains why.

### Step 3: Analyze fit (JD from TXT file)

Use the JD file contents as `jd_text`. With **jq** (recommended):

```bash
# Set your session_id from step 1
SESSION_ID="a1b2c3d4"

curl -s -X POST http://localhost:8000/analyze/fit \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg sid "$SESSION_ID" \
    --rawfile jd test_fixtures/jd.txt \
    '{ session_id: $sid, target_role: "SWE", use_curated_jd: false, jd_text: $jd }')"
```

Without **jq**, use Python to build JSON safely (handles newlines and quotes):

```bash
SESSION_ID="a1b2c3d4"
curl -s -X POST http://localhost:8000/analyze/fit \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
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

Use `test_fixtures/jd.txt` or your own path. Use `DS`, `MLE`, or `OTHER` for `target_role` as needed.

### Step 4 (optional): Generate tailored resume

Same idea: pass `jd_text` from your JD file.

```bash
curl -s -X POST http://localhost:8000/resume/generate \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg sid "$SESSION_ID" \
    --rawfile jd test_fixtures/jd.txt \
    '{ session_id: $sid, target_role: "SWE", use_curated_jd: false, jd_text: $jd }')"
```

### Step 5 (optional): Match by cluster

Per-cluster JD match percentage and evidence (requires processed resume with extraction + clusters):

```bash
curl -s -X POST http://localhost:8000/analyze/match-by-cluster \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg sid "$SESSION_ID" --rawfile jd test_fixtures/jd.txt \
    '{ session_id: $sid, use_curated_jd: false, jd_text: $jd }')"
```

---

## 2. Additional materials

Use **`POST /resume/materials/add`** (form: `session_id` + file or text) or **`POST /resume/materials/add/json`** (JSON: `session_id`, `text`). The backend merges new content into the session resume and re-runs the pipeline (chunk → extract → cluster → index). Poll **`/resume/status?upload_id=...`** as with resume upload.

### Add materials after resume upload

1. Upload resume (PDF or text) as in §1, poll until `ready`, and note `session_id`.
2. Add materials:

   ```bash
   curl -s -X POST http://localhost:8000/resume/materials/add/json \
     -H "Content-Type: application/json" \
     -d "$(jq -n --arg sid "YOUR_SESSION_ID" --rawfile text /path/to/materials.txt '{ session_id: $sid, text: $text }')"
   ```
3. Poll **`/resume/status?upload_id=...`** until `ready`, then run analyze/generate or match-by-cluster as below.

### Optional workaround: merge resume + materials into one upload

If you prefer a single upload (no add-materials flow), concatenate resume + materials and upload as text. E.g. `cat test_fixtures/resume.txt test_fixtures/materials.txt > /tmp/combined.txt` (or `pdftotext test_fixtures/resume.pdf - | cat - test_fixtures/materials.txt`), then `POST /resume/upload/json` with `combined.txt`.

---

## 3. Automated script

Use the helper script to run the full flow (upload → poll → analyze) from local files:

```bash
./scripts/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt
# With materials:
./scripts/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt -m test_fixtures/materials.txt
```

Specify paths with **`-r` / `--resume`**, **`-j` / `--jd`**, and optionally **`-m` / `--materials`**. Use `-h` or `--help` for usage.

- **resume** – Your `resume.pdf` or `resume.txt` (e.g. `test_fixtures/`).
- **jd** – Job description file (e.g. `test_fixtures/jd.txt`).
- **materials** – Optional; if provided, merged with resume and uploaded as text. With a PDF resume, `pdftotext` is required.

The script prints the analyze-fit JSON response. It expects the backend at `http://localhost:8000` and uses `jq` or Python for safe JSON.

---

## 4. Summary

| Input            | Where / how                                                       |
|------------------|-------------------------------------------------------------------|
| Resume PDF       | `test_fixtures/resume.pdf` (you add it) → `curl -F "file=@..."` or script |
| Resume TXT       | `test_fixtures/resume.txt` → `curl` + `/resume/upload/json`       |
| JD TXT           | `test_fixtures/jd.txt` (sample included) → `jd_text` in API       |
| Additional TXT   | `test_fixtures/materials.txt` → add-materials or merge upload     |
