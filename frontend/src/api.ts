/**
 * API client for Tech Career Fit Engine backend
 */

const API_BASE = '/api';

// === Types ===
export type RoleType = 'DS' | 'MLE' | 'SWE' | 'OTHER';
export type UploadStatus = 'uploading' | 'parsing' | 'chunking' | 'embedding' | 'indexing' | 'ready' | 'error';

export interface JDItem {
  title: string;
  role: RoleType;
  level: string;
  text: string;
}

export interface ResumeUploadResponse {
  session_id: string;
  upload_id: string;
}

export interface ResumeStatusResponse {
  upload_id: string;
  status: UploadStatus;
  detail: string;
}

export interface EvidenceChunk {
  chunk_id: string;
  text: string;
  source: string;
  score: number;
}

export interface Evidence {
  resume_chunks: EvidenceChunk[];
  jd_chunks: EvidenceChunk[];
}

export interface RoleRecommendation {
  role: string;
  score: number;
  reasons: string[];
}

export interface Requirements {
  must_have: string[];
  nice_to_have: string[];
}

export interface GapAnalysis {
  matched: string[];
  missing: string[];
  ask_user_questions: string[];
}

export interface AnalyzeFitResponse {
  recommended_roles: RoleRecommendation[];
  requirements: Requirements;
  gap: GapAnalysis;
  evidence: Evidence;
}

export interface ResumeStructured {
  education: string[];
  experience: string[];
  skills: string[];
}

export interface ResumeGenerateResponse {
  resume_markdown: string;
  resume_structured: ResumeStructured;
  need_info: string[];
  evidence: Evidence;
}

// === API Functions ===

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

// Ingest JDs
export async function ingestJDs(items: JDItem[]): Promise<{ status: string; jd_count_added: number }> {
  const res = await fetch(`${API_BASE}/jd/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Upload resume (text via JSON)
export async function uploadResumeText(text: string, sessionId?: string): Promise<ResumeUploadResponse> {
  const res = await fetch(`${API_BASE}/resume/upload/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, session_id: sessionId })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Upload resume (file)
export async function uploadResumeFile(file: File, sessionId?: string): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) formData.append('session_id', sessionId);
  
  const res = await fetch(`${API_BASE}/resume/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Check resume processing status
export async function getResumeStatus(uploadId: string): Promise<ResumeStatusResponse> {
  const res = await fetch(`${API_BASE}/resume/status?upload_id=${encodeURIComponent(uploadId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Poll until ready or error
export async function waitForResumeReady(
  uploadId: string,
  onStatusChange?: (status: ResumeStatusResponse) => void,
  maxWaitMs: number = 120000,
  pollIntervalMs: number = 1000
): Promise<ResumeStatusResponse> {
  const start = Date.now();
  
  while (Date.now() - start < maxWaitMs) {
    const status = await getResumeStatus(uploadId);
    if (onStatusChange) onStatusChange(status);
    
    if (status.status === 'ready' || status.status === 'error') {
      return status;
    }
    
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
  }
  
  throw new Error('Timeout waiting for resume processing');
}

// Analyze fit
export async function analyzeFit(
  sessionId: string,
  targetRole: RoleType,
  useCuratedJd: boolean,
  jdText?: string,
  jdUrl?: string
): Promise<AnalyzeFitResponse> {
  const res = await fetch(`${API_BASE}/analyze/fit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      target_role: targetRole,
      use_curated_jd: useCuratedJd,
      jd_text: jdText,
      jd_url: jdUrl
    })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Generate resume
export async function generateResume(
  sessionId: string,
  targetRole: RoleType,
  useCuratedJd: boolean,
  jdText?: string,
  jdUrl?: string
): Promise<ResumeGenerateResponse> {
  const res = await fetch(`${API_BASE}/resume/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      target_role: targetRole,
      use_curated_jd: useCuratedJd,
      jd_text: jdText,
      jd_url: jdUrl
    })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Export resume as .docx
export async function exportDocx(
  sessionId: string,
  targetRole: RoleType,
  useCuratedJd: boolean,
  jdText?: string,
  jdUrl?: string
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/resume/export_docx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      target_role: targetRole,
      use_curated_jd: useCuratedJd,
      jd_text: jdText,
      jd_url: jdUrl
    })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

// === Clustering Types ===
export interface ExperienceItem {
  id: string;
  label: string;
  text: string;
  source: string;
}

export interface ClusteredGroup {
  cluster_id: string;
  cluster_label: string;
  items: ExperienceItem[];
  summary: string;
}

export interface ClusterResponse {
  session_id: string;
  clusters: ClusteredGroup[];
  total_items: number;
}

// Cluster experience items
export async function clusterExperience(
  items: ExperienceItem[],
  resumeText?: string,
  sessionId?: string
): Promise<ClusterResponse> {
  const res = await fetch(`${API_BASE}/experience/cluster`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      items,
      resume_text: resumeText
    })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
