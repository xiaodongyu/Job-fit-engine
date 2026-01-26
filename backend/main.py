"""FastAPI application with all endpoints."""
import json
import re
import time
import uuid
from urllib.parse import urlparse, parse_qs
import html as html_lib

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from models import (
    JDIngestRequest, JDIngestResponse,
    ResumeUploadTextRequest, ResumeUploadResponse, ResumeStatusResponse,
    AnalyzeFitRequest, AnalyzeFitResponse,
    RoleRecommendation, Requirements, GapAnalysis, Evidence,
    ResumeGenerateRequest, ResumeGenerateResponse, ResumeStructured,
    HealthResponse, UploadStatus,
    ClusterRequest, ClusterResponse, ClusteredGroup, ExperienceItem
)
from prompts import (
    ROLE_FIT_SYSTEM, ROLE_FIT_SCHEMA,
    RESUME_GENERATE_SYSTEM, RESUME_GENERATE_SCHEMA,
    build_fit_prompt, build_generate_prompt
)
import rag
import gemini_client

app = FastAPI(title="Tech Career Fit Engine", version="0.2.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_linkedin_job_url(url: str) -> str:
    """
    Extract job_id from a LinkedIn job URL and return
    https://www.linkedin.com/jobs/view/{job_id}
    """
    parsed = urlparse(url)

    # 1️⃣ Case 1: /jobs/view/{job_id}
    match = re.search(r"/jobs/view/(\d+)", parsed.path)
    if match:
        job_id = match.group(1)
        return f"https://www.linkedin.com/jobs/view/{job_id}"

    # 2️⃣ Case 2: query param like ?currentJobId=123
    query = parse_qs(parsed.query)
    if "currentJobId" in query:
        job_id = query["currentJobId"][0]
        return f"https://www.linkedin.com/jobs/view/{job_id}"

    raise ValueError("Could not extract job_id from LinkedIn URL")

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_linkedin_jd_from_html(page_html: str) -> str:
    soup = BeautifulSoup(page_html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("@type") != "JobPosting":
                continue
            description = candidate.get("description")
            if not description:
                continue
            description = html_lib.unescape(description)
            text = BeautifulSoup(description, "html.parser").get_text(" ", strip=True)
            text = normalize_text(text)
            if text:
                return text

    selectors = [
        "div.show-more-less-html__markup",
  #      "div.description__text",
  #      "section.description",
  #      "div.jobs-description__content",
  #      "div.jobs-box__html-content",
  #      "div#job-details",
  #      "main",
    ]

    best = ""
    for selector in selectors:
        for element in soup.select(selector):
            text = normalize_text(element.get_text(" ", strip=True))
            if len(text) > len(best):
                best = text

    if not best:
        best = normalize_text(soup.get_text(" ", strip=True))

    return best


def fetch_linkedin_jd_text(url: str) -> str:
    url = normalize_linkedin_job_url(url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="LinkedIn URL must start with http or https")

    host = parsed.netloc.lower()
    if "linkedin.com" not in host:
        raise HTTPException(status_code=400, detail="Only LinkedIn job URLs are supported")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch LinkedIn URL: {exc}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"LinkedIn request failed with status {response.status_code}"
        )

    text = extract_linkedin_jd_from_html(response.text)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract job description from LinkedIn page")

    return text[:20000]


def wait_for_upload_ready(upload_id: str, timeout_seconds: int = 60, poll_interval: float = 0.25) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        status_info = rag.get_upload_status(upload_id)
        status = status_info.get("status")
        if status == UploadStatus.READY:
            return
        if status == UploadStatus.ERROR:
            detail = status_info.get("detail", "Job description processing failed")
            raise HTTPException(status_code=400, detail=detail)
        time.sleep(poll_interval)
    raise HTTPException(status_code=504, detail="Timed out processing LinkedIn job description")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", message="Tech Career Fit Engine is running")


@app.post("/jd/ingest", response_model=JDIngestResponse)
async def jd_ingest(request: JDIngestRequest):
    """Ingest JD items into global FAISS index."""
    try:
        items = [item.model_dump() for item in request.items]
        count = rag.ingest_jds(items)
        return JDIngestResponse(status="ok", jd_count_added=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume/upload", response_model=ResumeUploadResponse)
async def resume_upload(
    file: UploadFile = File(None),
    text: str = Form(None),
    session_id: str = Form(None)
):
    """Upload resume via file or text. Returns upload_id for status tracking."""
    # Determine content
    resume_text = None
    
    if file:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        try:
            resume_text = rag.parse_file(content, file.filename or "unknown.txt")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")
    elif text:
        resume_text = text
    else:
        raise HTTPException(status_code=400, detail="Either file or text must be provided")
    
    if not resume_text or not resume_text.strip():
        raise HTTPException(status_code=400, detail="No text content found in upload")
    
    # Generate session_id if not provided
    if not session_id:
        session_id = uuid.uuid4().hex[:8]
    
    try:
        # Start background processing
        upload_id = rag.start_resume_processing(session_id, resume_text)
        
        return ResumeUploadResponse(
            session_id=session_id,
            upload_id=upload_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume/upload/json", response_model=ResumeUploadResponse)
async def resume_upload_json(request: ResumeUploadTextRequest):
    """Upload resume via JSON body."""
    session_id = request.session_id or uuid.uuid4().hex[:8]
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")
    
    try:
        upload_id = rag.start_resume_processing(session_id, request.text)
        
        return ResumeUploadResponse(
            session_id=session_id,
            upload_id=upload_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resume/status", response_model=ResumeStatusResponse)
async def resume_status(upload_id: str = Query(...)):
    """Get resume processing status."""
    status_info = rag.get_upload_status(upload_id)
    return ResumeStatusResponse(
        upload_id=upload_id,
        status=status_info["status"],
        detail=status_info.get("detail", "")
    )


@app.post("/analyze/fit", response_model=AnalyzeFitResponse)
async def analyze_fit(request: AnalyzeFitRequest):
    """Analyze resume fit against JD requirements."""
    # Check session is ready
    if not rag.session_is_ready(request.session_id):
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} resume not ready. Check /resume/status.")
    
    try:
        # Build query from target role
        query = f"Skills and experience for {request.target_role} role"
        
        # Retrieve resume evidence
        resume_chunks = rag.search_resume_index(request.session_id, query)
        
        # Retrieve JD evidence
        if request.use_curated_jd:
            jd_chunks = rag.search_jd_index(query, role=request.target_role)
            if not jd_chunks:
                raise HTTPException(status_code=400, detail="No curated JDs found. Ingest JDs first or provide jd_text.")
        elif request.jd_text:
            jd_chunks = rag.search_temp_jd(request.jd_text, query)
        elif request.jd_url:
            jd_text = fetch_linkedin_jd_text(request.jd_url)
            jd_session_id = f"{request.session_id}_jd"
            upload_id = rag.start_resume_processing(jd_session_id, jd_text)
            wait_for_upload_ready(upload_id)
            jd_chunks = rag.search_resume_index(jd_session_id, query, source_label="jd")
        else:
            raise HTTPException(status_code=400, detail="Either use_curated_jd=true or provide jd_text or jd_url")
        
        # Build prompt and call Gemini
        user_prompt = build_fit_prompt(resume_chunks, jd_chunks, request.target_role)
        result = gemini_client.generate(ROLE_FIT_SYSTEM, user_prompt, ROLE_FIT_SCHEMA)
        
        content = result.get("content", {})
        if isinstance(content, str):
            content = {}
        
        # Build response
        recommended_roles = []
        for r in content.get("recommended_roles", []):
            recommended_roles.append(RoleRecommendation(
                role=r.get("role", request.target_role),
                score=min(1.0, max(0.0, r.get("score", 0.5))),
                reasons=r.get("reasons", [])
            ))
        
        if not recommended_roles:
            recommended_roles.append(RoleRecommendation(
                role=request.target_role,
                score=0.5,
                reasons=["Analysis based on provided evidence"]
            ))
        
        reqs = content.get("requirements", {})
        gap = content.get("gap", {})
        
        return AnalyzeFitResponse(
            recommended_roles=recommended_roles,
            requirements=Requirements(
                must_have=reqs.get("must_have", []),
                nice_to_have=reqs.get("nice_to_have", [])
            ),
            gap=GapAnalysis(
                matched=gap.get("matched", []),
                missing=gap.get("missing", []),
                ask_user_questions=gap.get("ask_user_questions", [])
            ),
            evidence=Evidence(
                resume_chunks=resume_chunks,
                jd_chunks=jd_chunks
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_resume_internal(request: ResumeGenerateRequest) -> tuple:
    """Internal function to generate resume. Returns (structured, evidence)."""
    query = f"Complete background for {request.target_role} position"
    
    # Retrieve evidence
    resume_chunks = rag.search_resume_index(request.session_id, query)
    
    if request.use_curated_jd:
        jd_chunks = rag.search_jd_index(query, role=request.target_role)
    elif request.jd_text:
        jd_chunks = rag.search_temp_jd(request.jd_text, query)
    elif request.jd_url:
        jd_text = fetch_linkedin_jd_text(request.jd_url)
        jd_session_id = f"{request.session_id}_jd"
        upload_id = rag.start_resume_processing(jd_session_id, jd_text)
        wait_for_upload_ready(upload_id)
        jd_chunks = rag.search_resume_index(jd_session_id, query, source_label="jd")
    else:
        jd_chunks = []
    
    # Build prompt and generate
    user_prompt = build_generate_prompt(resume_chunks, jd_chunks, request.target_role)
    result = gemini_client.generate(RESUME_GENERATE_SYSTEM, user_prompt, RESUME_GENERATE_SCHEMA)
    
    content = result.get("content", {})
    if isinstance(content, str):
        content = {"education": [], "experience": [], "skills": [], "need_info": []}
    
    # Extract structured data
    education = content.get("education", [])
    experience = content.get("experience", [])
    skills = content.get("skills", [])
    need_info = content.get("need_info", [])
    
    structured = ResumeStructured(
        education=education,
        experience=experience,
        skills=skills
    )
    
    evidence = Evidence(
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks
    )
    
    return structured, need_info, evidence


def build_markdown_from_structured(structured: ResumeStructured) -> str:
    """Build markdown resume from structured data."""
    lines = []
    
    lines.append("## Education")
    if structured.education:
        for item in structured.education:
            lines.append(f"- {item}")
    else:
        lines.append("_No education information available._")
    
    lines.append("")
    lines.append("## Experience")
    if structured.experience:
        for item in structured.experience:
            lines.append(f"- {item}")
    else:
        lines.append("_No experience information available._")
    
    lines.append("")
    lines.append("## Skills")
    if structured.skills:
        lines.append(", ".join(structured.skills))
    else:
        lines.append("_No skills information available._")
    
    return "\n".join(lines)


@app.post("/resume/generate", response_model=ResumeGenerateResponse)
async def resume_generate(request: ResumeGenerateRequest):
    """Generate tailored resume based on evidence."""
    # Check session is ready
    if not rag.session_is_ready(request.session_id):
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} resume not ready.")
    
    try:
        structured, need_info, evidence = generate_resume_internal(request)
        resume_markdown = build_markdown_from_structured(structured)
        
        return ResumeGenerateResponse(
            resume_markdown=resume_markdown,
            resume_structured=structured,
            need_info=need_info,
            evidence=evidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume/export_docx")
async def resume_export_docx(request: ResumeGenerateRequest):
    """Generate and export resume as .docx file."""
    from fastapi.responses import Response
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from io import BytesIO
    
    # Check session is ready
    if not rag.session_is_ready(request.session_id):
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} resume not ready.")
    
    try:
        structured, need_info, _ = generate_resume_internal(request)
        
        # Create Word document
        doc = Document()
        
        # Title
        title = doc.add_heading("Resume", level=0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Education section
        doc.add_heading("Education", level=1)
        if structured.education:
            for item in structured.education:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(item)
        else:
            doc.add_paragraph("No education information available.", style='Normal')
        
        # Experience section
        doc.add_heading("Experience", level=1)
        if structured.experience:
            for item in structured.experience:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(item)
        else:
            doc.add_paragraph("No experience information available.", style='Normal')
        
        # Skills section
        doc.add_heading("Skills", level=1)
        if structured.skills:
            skills_text = ", ".join(structured.skills)
            doc.add_paragraph(skills_text, style='Normal')
        else:
            doc.add_paragraph("No skills information available.", style='Normal')
        
        # Need Info section (if any)
        if need_info:
            doc.add_heading("Information Needed", level=1)
            for item in need_info:
                p = doc.add_paragraph(style='List Bullet')
                run = p.add_run(item)
                run.italic = True
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=resume.docx"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CLUSTERING ENDPOINTS (PLACEHOLDER)
# =============================================================================

@app.post("/experience/cluster", response_model=ClusterResponse)
async def cluster_experience(request: ClusterRequest):
    """
    Cluster user's experience items (stickers, texts, resume chunks).
    
    Data sources:
    1. items: Stickers and other experience items from frontend
    2. resume_text: Optional pasted resume text
    3. session_id: If provided and valid, retrieves uploaded resume chunks from session
    
    PLACEHOLDER IMPLEMENTATION: Returns all items in a single cluster.
    TODO: Implement actual clustering algorithm (e.g., k-means, hierarchical, etc.)
    """
    session_id = request.session_id or uuid.uuid4().hex[:8]
    
    # Collect all items
    all_items: list[ExperienceItem] = list(request.items)
    
    # If resume_text is provided (pasted text), add it as a single item
    if request.resume_text and request.resume_text.strip():
        all_items.append(ExperienceItem(
            id=f"pasted_{uuid.uuid4().hex[:6]}",
            label="resume",
            text=request.resume_text.strip(),
            source="pasted_text"
        ))
    
    # If session_id is provided and has uploaded resume data, retrieve those chunks
    if request.session_id and rag.session_is_ready(request.session_id):
        resume_chunks = rag.get_all_resume_chunks(request.session_id)
        for chunk in resume_chunks:
            all_items.append(ExperienceItem(
                id=chunk.get("chunk_id", f"chunk_{uuid.uuid4().hex[:6]}"),
                label="resume",
                text=chunk.get("text", ""),
                source="uploaded_resume"
            ))
    
    # PLACEHOLDER: Put all items into one cluster
    # TODO: Replace with actual clustering algorithm
    single_cluster = ClusteredGroup(
        cluster_id="cluster_0",
        cluster_label="All Experiences",
        items=all_items,
        summary="All user experiences grouped together (placeholder - no clustering applied)"
    )
    
    return ClusterResponse(
        session_id=session_id,
        clusters=[single_cluster],
        total_items=len(all_items)
    )


if __name__ == "__main__":
    import os
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
