# Deployment Log

Summary of deployment work for the Tech Career Fit Engine: fixing Vercel NOT_FOUND, wiring frontend to a separate backend, and deploying the backend on Render (free tier).

---

## 1. Problem: Vercel NOT_FOUND

When deploying from the repo root, the deployed site returned **NOT_FOUND** (404). The app lives in `frontend/` (Vite + React), but Vercel by default uses the **repository root** as the project root. There is no `package.json` at repo root, so Vercel had no build/output to serve.

---

## 2. Fix: Vercel configuration

**Root-level `vercel.json`** (repo root):

- **`installCommand`:** `cd frontend && npm install` — install dependencies in `frontend/`
- **`buildCommand`:** `cd frontend && npm run build` — build the Vite app
- **`outputDirectory`:** `frontend/dist` — serve the built static files from here
- **`framework`:** `null` — avoid framework auto-detection at repo root
- **`rewrites`:** `{ "source": "/(.*)", "destination": "/index.html" }` — SPA fallback: any path that doesn’t match a static file serves `index.html`

With this, the project can be deployed from repo root without changing the Vercel “Root Directory” in the dashboard.

**`frontend/vercel.json`** (alternative):

- Contains only the same **`rewrites`** for SPA fallback.
- Use this when you set **Root Directory** to `frontend` in Vercel Project Settings; then Vercel auto-detects Vite and uses this file for routing.

---

## 3. Architecture: Frontend on Vercel, backend elsewhere

- **Frontend:** Deployed on **Vercel** (static build from `frontend/`).
- **Backend:** Deployed on a **separate host** (chosen: **Render** free tier). The existing FastAPI app runs unchanged; no backend code changes for deployment.
- **Connection:** The frontend calls the backend via a configurable base URL. Locally: `/api` (Vite proxy to `localhost:8000`). In production: the backend’s public URL, set via an environment variable.

---

## 4. Frontend: Configurable API base

**File:** `frontend/src/api.ts`

- **Change:** `const API_BASE = '/api';` → `const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';`
- **Local:** No `VITE_API_BASE` → uses `'/api'` → Vite dev server proxies to the local backend.
- **Production (Vercel):** Set **`VITE_API_BASE`** in the Vercel project (Settings → Environment Variables) to the backend URL, e.g. `https://your-service-name.onrender.com` (no trailing slash). Redeploy so the build picks up the variable.

Vite only exposes env vars prefixed with `VITE_`, so the name must be `VITE_API_BASE`.

---

## 5. Backend on Render (free tier)

**Why Render:** Easiest for someone with no deployment experience: all in the browser, no Docker, free tier (750 hours/month; service sleeps after inactivity).

**Render Web Service setup:**

| Setting | Value |
|--------|--------|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

**Environment variables (Render dashboard):** Add at least `GEMINI_API_KEY`; add others from `backend/env.template` if you need to override defaults. Render sets `PORT`; the start command uses it.

**Build fix (Render / Python 3.13):** `faiss-cpu==1.9.0` had no matching distribution on Render’s environment. **Change in `backend/requirements.txt`:** `faiss-cpu==1.9.0` → `faiss-cpu==1.9.0.post1`. No code changes; API-compatible.

After deploy, Render gives a URL (e.g. `https://your-service-name.onrender.com`). Use that as `VITE_API_BASE` in Vercel.

---

## 6. Current state (quick reference)

| Component | Where | Config / Notes |
|-----------|--------|----------------|
| Frontend | Vercel | Root `vercel.json` or Root Directory = `frontend` + `frontend/vercel.json`; set `VITE_API_BASE` to backend URL |
| Backend | Render (free) | Root dir `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`; `faiss-cpu==1.9.0.post1` |
| API base (prod) | Vercel env | `VITE_API_BASE` = Render service URL (no trailing slash) |

Backend CORS is already `allow_origins=["*"]`, so the Vercel frontend origin is allowed.

---

## 7. Files touched (deployment)

| Area | Files |
|------|--------|
| Vercel | `vercel.json` (root), `frontend/vercel.json` |
| Frontend API | `frontend/src/api.ts` (use `VITE_API_BASE`) |
| Backend deps | `backend/requirements.txt` (`faiss-cpu==1.9.0.post1`) |
| Docs | `docs/deployment_log.md` (this file) |

---

## 8. Post-commit: going live

Summary of what was done **after** the "prepare for deployment" commit (backend branch merged to main, then pushed):

1. **Push to fork** — Pushed `main` to the **fork** remote (`git push fork main`) so Render could pull the latest code (including the `faiss-cpu==1.9.0.post1` fix).
2. **Backend redeploy on Render** — Triggered a new deploy on Render (e.g. from the latest push to `main`, or via Manual Deploy). Build took several minutes (normal for `pip install` with heavier deps); deployment succeeded.
3. **Wire frontend to backend** — In Vercel → frontend project → Settings → Environment Variables, set **`VITE_API_BASE`** to the Render service URL (no trailing slash). Redeployed the frontend so the production build uses that URL.
4. **Frontend deployment** — Frontend redeploy on Vercel succeeded.
5. **Outcome** — The app is now accessible from a **public URL** (Vercel frontend) instead of localhost; production frontend talks to the Render backend. First request after backend sleep (free tier) may take 30–60 seconds to wake the service.

---

## 9. Homework: LLM API documentation and verification

Summary of work for the backend homework (将 API 调用拆分、调用大模型 API、封装 REST API、提交说明文档与截图).

### 9.1 Homework requirements vs implementation

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Separate API calling logic | Met | `backend/gemini_client.py` |
| Call LLM APIs | Met | Google Gemini (Embedding + Generation) |
| API Key self-provided | Met | `GEMINI_API_KEY` in `.env` |
| Backend as REST API | Met | FastAPI with 15+ endpoints |
| Frontend integration | Met | `frontend/src/api.ts` |

### 9.2 Files created or updated

**New files:**

| File | Purpose |
|------|---------|
| `docs/大模型API调用说明.md` | Main API doc: product intro, API list, call scenarios, Mermaid diagram, env config, screenshot instructions |
| `tests/verify_api_for_screenshots.sh` | Script to run health check, upload resume, `/analyze/fit`, `/resume/generate` for screenshots |

**Updated files:**

| File | Changes |
|------|---------|
| `README.md` | Added “大模型 API 调用” section linking to `docs/大模型API调用说明.md` |
| `docs/大模型API调用说明.md` | Section 7: two ways to capture screenshots (script vs manual) |
| `docs/verify_api_output.md` | Updated script path to `./tests/verify_api_for_screenshots.sh` |
| `tests/verify_api_for_screenshots.sh` | Usage comments updated for `tests/` location |
| `tests/README.md` | Added script as item 6 and Quick reference row |

### 9.3 Documentation structure (`docs/大模型API调用说明.md`)

1. 产品简介
2. 大模型 API 列表 (Embedding + Generation)
3. API 封装与拆分 + Mermaid 调用架构图
4. 调用场景一览 (Embedding & Generation 调用点)
5. 环境配置 (`GEMINI_API_KEY`, etc.)
6. REST API 端点一览
7. 截图与验证建议 (script + manual curl steps)
8. GitHub 与部署

### 9.4 Verification script flow

`tests/verify_api_for_screenshots.sh` runs in sequence:

1. `GET /health`
2. `POST /resume/upload/json`
3. Poll `/resume/status` until `ready`
4. `POST /analyze/fit`
5. `POST /resume/generate`

### 9.5 Homework submission checklist

| Deliverable | Status |
|-------------|--------|
| 说明文档（调用了哪些大模型 API） | Done: `docs/大模型API调用说明.md` |
| 截图（API 调用 + REST API 正常） | Pending: run script or manual curl, then screenshot |
| GitHub Link | Pending: add repo URL to submission |
