# Collaborations Log

## 2025-02-04 — Branch merges and contributor integration

### Summary

Integrated multiple branches and contributor work into `main` on fork (xiaodongyu/Job-fit-engine). Merged backend, Ui/UX, upstream Update22, and mike890505-cmd's MVP2 branch.

---

### 1. Backend branch

- **Committed** local changes to `backend`: doc renames (`backend_log.md`, `backend_prompt.md`), API doc updates, commit message "prepare to merge with Ui/UX"
- **Pushed** `backend` to fork
- **Merged** `backend` into `main` (deployment, API docs, architecture summary, curated JD ingestion)

---

### 2. Ui/UX branch (Peter Zhou)

- **Merged** `fork/Ui/UX` into integration branch `merge-backend-uiux`:
  - Landing page (`Landing.tsx`)
  - Dot shader background (`dot-shader-background.tsx`)
  - Container scroll animation
  - Tailwind, PostCSS, Vite config updates

---

### 3. Integration branch

- **Created** `merge-backend-uiux` from `main`
- **Pulled** from origin (Merrermer) — already up to date
- **Merged** backend then Ui/UX into `merge-backend-uiux`
- **Merged** `merge-backend-uiux` into `main` with message "Merge integration: backend + Ui/UX"
- **Pushed** to fork

---

### 4. Update22 from upstream (Merrermer)

- **Fetched** `origin`
- **Merged** `origin/Update22` into `main`:
  - Curated JD bug fix
  - Resume structure test
  - `ingest_curated_jds.py`, `main.py`, `prompts.py`, `rag.py` updates
  - `test_two_pass_parsing.py`
- **Pushed** to fork

---

### 5. MVP2 from contributor (mike890505-cmd)

- **Added** remote: `mike` → https://github.com/mike890505-cmd/career-fit-engine.git
- **Fetched** `mike MVP2`
- **Merged** `mike/MVP2` into `main` with conflict resolution:
  - `backend/main.py`: Combined imports (asynccontextmanager, Path + re, time, BeautifulSoup, requests for LinkedIn JD scraping)
  - `backend/requirements.txt`: Kept requests, pytest; added beautifulsoup4
  - `frontend/src/App.tsx`: Kept Landing, DotScreenShader; added CareerFitState type
  - `frontend/src/types.ts`: Kept `'landing'` in Step; added `'linkedin'` to JDSource
- **Features** from MVP2: LinkedIn job URL support, JD extraction from HTML (BeautifulSoup)
- **Pushed** to fork

---

### Remote configuration

| Remote | URL |
|--------|-----|
| `origin` | https://github.com/Merrermer/Job-fit-engine.git |
| `fork` | git@github.com:xiaodongyu/Job-fit-engine.git |
| `mike` | https://github.com/mike890505-cmd/career-fit-engine.git |

---

### Current state

- `main` includes backend, Ui/UX, Update22, and MVP2
- `main` is ahead of `origin/main` (upstream) — PR can be opened for contribution back
- `main` is in sync with `fork/main` (pushed)
