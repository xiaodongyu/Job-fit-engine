"""Pydantic models for request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


# === Enums ===
class RoleType(str, Enum):
    DS = "DS"
    MLE = "MLE"
    SWE = "SWE"
    OTHER = "OTHER"


class LevelType(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    ANY = "any"


class UploadStatus(str, Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


# === JD Ingest ===
class JDItem(BaseModel):
    title: str
    role: RoleType
    level: LevelType = LevelType.ANY
    text: str


class JDIngestRequest(BaseModel):
    items: list[JDItem]


class JDIngestResponse(BaseModel):
    status: str = "ok"
    jd_count_added: int


# === Resume Upload ===
class ResumeUploadTextRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    session_id: str
    upload_id: str


class ResumeStatusResponse(BaseModel):
    upload_id: str
    status: UploadStatus
    detail: str = ""


# === Evidence Chunk ===
class EvidenceChunk(BaseModel):
    chunk_id: str
    text: str
    source: str  # "resume" or "jd"
    score: float


class Evidence(BaseModel):
    resume_chunks: list[EvidenceChunk]
    jd_chunks: list[EvidenceChunk]


# === Analyze Fit ===
class AnalyzeFitRequest(BaseModel):
    session_id: str
    target_role: RoleType
    use_curated_jd: bool = False
    jd_text: Optional[str] = None


class RoleRecommendation(BaseModel):
    role: str
    score: float = Field(ge=0, le=1)
    reasons: list[str]


class Requirements(BaseModel):
    must_have: list[str]
    nice_to_have: list[str]


class GapAnalysis(BaseModel):
    matched: list[str]
    missing: list[str]
    ask_user_questions: list[str]


class AnalyzeFitResponse(BaseModel):
    recommended_roles: list[RoleRecommendation]
    requirements: Requirements
    gap: GapAnalysis
    evidence: Evidence


# === Resume Generate ===
class ResumeGenerateRequest(BaseModel):
    session_id: str
    target_role: RoleType
    use_curated_jd: bool = False
    jd_text: Optional[str] = None


class ResumeStructured(BaseModel):
    education: list[str]
    experience: list[str]
    skills: list[str]


class ResumeGenerateResponse(BaseModel):
    resume_markdown: str
    resume_structured: ResumeStructured
    need_info: list[str]
    evidence: Evidence


# === Health ===
class HealthResponse(BaseModel):
    status: str
    message: str


# === Experience Clustering ===
class ExperienceItem(BaseModel):
    """A single experience item (sticker, text snippet, etc.)"""
    id: str
    label: str  # e.g., 'work', 'project', 'skill', 'education', etc.
    text: str
    source: str = "sticker"  # 'sticker', 'pasted_text', 'resume_chunk'


class ClusterRequest(BaseModel):
    """Request to cluster user's experience items."""
    session_id: Optional[str] = None
    items: list[ExperienceItem]
    resume_text: Optional[str] = None  # Optional pasted resume text


class ClusteredGroup(BaseModel):
    """A cluster of related experience items."""
    cluster_id: str
    cluster_label: str  # e.g., 'Technical Skills', 'Work Experience', etc.
    items: list[ExperienceItem]
    summary: str = ""  # Optional summary of the cluster


class ClusterResponse(BaseModel):
    """Response containing clustered experience items."""
    session_id: str
    clusters: list[ClusteredGroup]
    total_items: int
