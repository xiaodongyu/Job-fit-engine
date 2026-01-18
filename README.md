# Tech Career Fit Engine

AI-powered resume analyzer with **strict evidence grounding** using Gemini API + local FAISS RAG.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Gemini API Key** - Get one from [Google AI Studio](https://aistudio.google.com/apikey)

## TL;DR - Run the App

```powershell
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
Copy-Item env.template .env   # Then edit .env with your GEMINI_API_KEY
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

## Architecture

```
├── backend/               # FastAPI Python backend
│   ├── main.py            # API routes (7 endpoints)
│   ├── models.py          # Pydantic schemas
│   ├── prompts.py         # LLM prompts + JSON schemas
│   ├── gemini_client.py   # Gemini embed + generate
│   ├── rag.py             # FAISS index + chunking + parsing
│   ├── requirements.txt
│   ├── env.template
│   └── data/              # Runtime: FAISS indices + metadata
├── frontend/              # Vite + React TypeScript
│   ├── src/
│   │   ├── App.tsx        # Main shell with step routing
│   │   ├── api.ts         # API client
│   │   ├── types.ts       # TypeScript types & constants
│   │   ├── useCareerFit.ts # Custom hook (state + handlers)
│   │   ├── styles.css     # Dark theme UI
│   │   └── steps/         # Step page components
│   │       ├── StickerBoard.tsx
│   │       ├── RoleSelector.tsx
│   │       ├── AnalysisResults.tsx
│   │       └── ClusterView.tsx
│   └── package.json
```

## RAG Pipeline

```
Upload → Parse (PDF/DOCX/TXT) → Chunk → Embed (Gemini) → FAISS Index
```

- **Dual indices**: Global JD library + per-session resume
- **Cosine similarity**: Normalized embeddings + IndexFlatIP
- **Grounded outputs**: All claims traced to evidence chunks

## Quick Start

### 1. Backend Setup

```powershell
cd backend

# Create environment (conda or venv)
conda create -n career-fit python=3.11 -y
conda activate career-fit

# Or with venv:
# python -m venv venv
# .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item env.template .env
# Edit .env: set GEMINI_API_KEY=your-key-here

# Start server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000 (proxies to backend)

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Ingest Job Descriptions
```bash
curl -X POST http://localhost:8000/jd/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "title": "Senior Software Engineer",
        "role": "SWE",
        "level": "senior",
        "text": "5+ years Python, JavaScript, AWS. Microservices, REST APIs, SQL. Nice: Kubernetes, Docker."
      },
      {
        "title": "Data Scientist",
        "role": "DS",
        "level": "mid",
        "text": "Python, ML (scikit-learn, pandas), statistical analysis, A/B testing. Nice: deep learning, NLP."
      },
      {
        "title": "ML Engineer",
        "role": "MLE",
        "level": "senior",
        "text": "Production ML: Python, PyTorch, MLOps (MLflow), model serving. Nice: LLM fine-tuning."
      }
    ]
  }'
```

### Upload Resume (JSON)
```bash
curl -X POST http://localhost:8000/resume/upload/json \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe\nSoftware Engineer\n\n3 years at TechCorp: Python REST APIs, AWS migration, data pipelines with Pandas.\n\nSkills: Python, JavaScript, AWS, Docker, PostgreSQL\nEducation: BS Computer Science"
  }'
# Returns: { "session_id": "abc123", "upload_id": "xyz789" }
```

### Upload Resume (File)
```bash
curl -X POST http://localhost:8000/resume/upload \
  -F "file=@resume.pdf"
```

### Check Processing Status
```bash
curl "http://localhost:8000/resume/status?upload_id=xyz789"
# Returns: { "upload_id": "xyz789", "status": "ready", "detail": "Indexed 5 chunks" }
```

Status values: `uploading` → `parsing` → `chunking` → `embedding` → `indexing` → `ready` (or `error`)

### Analyze Fit (Custom JD)
```bash
curl -X POST http://localhost:8000/analyze/fit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "target_role": "SWE",
    "use_curated_jd": false,
    "jd_text": "Software Engineer: Python, AWS, 3+ years, API development."
  }'
```

### Analyze Fit (Curated JD Library)
```bash
curl -X POST http://localhost:8000/analyze/fit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "target_role": "SWE",
    "use_curated_jd": true
  }'
```

### Generate Tailored Resume
```bash
curl -X POST http://localhost:8000/resume/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "target_role": "SWE",
    "use_curated_jd": false,
    "jd_text": "Software Engineer with Python and cloud experience."
  }'
```

### Cluster Experience (Placeholder)
```bash
curl -X POST http://localhost:8000/experience/cluster \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "items": [
      { "id": "1", "label": "work", "text": "3 years at TechCorp building APIs", "source": "sticker" },
      { "id": "2", "label": "skill", "text": "Python, FastAPI, PostgreSQL", "source": "sticker" },
      { "id": "3", "label": "project", "text": "Built ML pipeline for recommendations", "source": "sticker" }
    ],
    "resume_text": "Optional pasted resume text here..."
  }'
# Returns: { "session_id": "...", "clusters": [...], "total_items": N }
```

Data sources for clustering:
- `items`: Stickers from the frontend
- `resume_text`: Optional pasted resume text
- `session_id`: If provided, also retrieves uploaded resume chunks from the session

> **Note:** This is a placeholder endpoint. Currently returns all items in a single cluster. TODO: Implement actual clustering algorithm.

## Grounding Rules

### Resume Claims
- ✅ Only include bullets supported by retrieved resume chunks
- ❌ Never fabricate skills/experiences
- 📝 Missing info → "Need Info" checklist

### JD Requirements
- ✅ Only extract from curated JD chunks or user-pasted JD
- ❌ Never invent "common requirements"
- 📋 Evidence chunks included in response

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GEMINI_API_KEY | Yes | - | Google AI API key |
| GEMINI_EMBED_MODEL | No | gemini-embedding-001 | Embedding model |
| GEMINI_GEN_MODEL | No | gemini-2.0-flash | Generation model |
| TOP_K | No | 6 | Number of chunks to retrieve |
| CHUNK_SIZE | No | 800 | Characters per chunk |
| CHUNK_OVERLAP | No | 120 | Overlap between chunks |
| APP_HOST | No | 0.0.0.0 | Server host |
| APP_PORT | No | 8000 | Server port |

## Data Storage

Runtime data stored in `backend/data/`:
```
data/
├── jd.index           # Global JD FAISS index
├── jd_meta.json       # JD chunk metadata
└── sessions/
    └── {session_id}/
        ├── resume.index      # Resume FAISS index
        └── resume_meta.json  # Resume chunk metadata
```

## Usage Flow

1. **Upload Resume** → Parse → Chunk → Embed → Index (with status polling)
2. **Select Target Role** → Choose DS/MLE/SWE/OTHER + JD source
3. **View Analysis** → Role fit scores + requirements + gap analysis + evidence
4. **Generate Resume** → Grounded bullets + "Need Info" checklist

**Optional:** Use "View Clusters" to see your experiences grouped (placeholder - actual clustering algorithm TBD)
