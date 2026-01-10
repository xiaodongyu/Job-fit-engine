"""System prompts and JSON schemas for structured outputs."""

# === Role Fit Analysis ===
ROLE_FIT_SYSTEM = """You are a career advisor analyzing resume-to-role fit.

CRITICAL GROUNDING RULES:
1. ONLY use the provided RESUME EVIDENCE chunks. Do NOT fabricate skills or experiences.
2. ONLY use the provided JD EVIDENCE chunks for requirements. Do NOT invent requirements.
3. Score must reflect ACTUAL overlap between resume evidence and JD requirements.
4. Reasons must cite specific evidence from the provided chunks.
5. If information is unclear or missing, add to ask_user_questions. Do NOT guess.

Analyze and return structured JSON."""

ROLE_FIT_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_roles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "score": {"type": "number"},
                    "reasons": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["role", "score", "reasons"]
            }
        },
        "requirements": {
            "type": "object",
            "properties": {
                "must_have": {"type": "array", "items": {"type": "string"}},
                "nice_to_have": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["must_have", "nice_to_have"]
        },
        "gap": {
            "type": "object",
            "properties": {
                "matched": {"type": "array", "items": {"type": "string"}},
                "missing": {"type": "array", "items": {"type": "string"}},
                "ask_user_questions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["matched", "missing", "ask_user_questions"]
        }
    },
    "required": ["recommended_roles", "requirements", "gap"]
}

# === Resume Generation ===
RESUME_GENERATE_SYSTEM = """You are a professional resume writer creating a tailored resume.

CRITICAL GROUNDING RULES:
1. ONLY include content DIRECTLY supported by the provided RESUME EVIDENCE.
2. Do NOT fabricate, embellish, or infer skills/experiences not in evidence.
3. If a JD requirement cannot be matched to resume evidence, add it to need_info.
4. Tailor language to match JD keywords, but NEVER add false claims.

RESUME WRITING STYLE:
- Use strong action verbs (Led, Developed, Implemented, Optimized, Designed, etc.)
- Write concise, impactful bullets
- Quantify impact when numbers are present in evidence (e.g., "increased performance by 40%")
- Tailor wording to target role and JD requirements
- Keep bullets professional and achievement-focused

OUTPUT STRUCTURE (required sections):
1. education: List of education entries from evidence
2. experience: List of experience bullets from evidence  
3. skills: List of skills mentioned in evidence

Return structured JSON with these exact sections."""

RESUME_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "education": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Education entries from resume evidence"
        },
        "experience": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Experience bullets with action verbs"
        },
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills extracted from evidence"
        },
        "need_info": {
            "type": "array",
            "items": {"type": "string"},
            "description": "JD requirements not found in resume evidence"
        }
    },
    "required": ["education", "experience", "skills", "need_info"]
}


def build_fit_prompt(
    resume_chunks: list[dict],
    jd_chunks: list[dict],
    target_role: str
) -> str:
    """Build user prompt for fit analysis."""
    resume_text = "\n\n".join([
        f"[{c.chunk_id}] {c.text}" for c in resume_chunks
    ])
    jd_text = "\n\n".join([
        f"[{c.chunk_id}] {c.text}" for c in jd_chunks
    ])
    
    return f"""TARGET ROLE: {target_role}

=== RESUME EVIDENCE ===
{resume_text}

=== JD EVIDENCE ===
{jd_text}

Analyze the fit between this candidate and the target role.
Extract requirements ONLY from JD evidence.
Match/gap analysis based ONLY on resume evidence.
Return JSON with recommended_roles, requirements, and gap."""


def build_generate_prompt(
    resume_chunks: list[dict],
    jd_chunks: list[dict],
    target_role: str
) -> str:
    """Build user prompt for resume generation."""
    resume_text = "\n\n".join([
        f"[{c.chunk_id}] {c.text}" for c in resume_chunks
    ])
    jd_text = "\n\n".join([
        f"[{c.chunk_id}] {c.text}" for c in jd_chunks
    ])
    
    return f"""TARGET ROLE: {target_role}

=== RESUME EVIDENCE (use ONLY this for content) ===
{resume_text}

=== JD EVIDENCE (align wording to these, do NOT invent facts) ===
{jd_text}

Generate a structured resume with EXACTLY these sections:

1. EDUCATION: Extract education entries from resume evidence
2. EXPERIENCE: Create impactful bullets using action verbs, quantify when data available
3. SKILLS: List relevant skills from resume evidence

Rules:
- Content must come from RESUME EVIDENCE only
- Tailor wording to JD but do NOT add claims not in evidence
- Use strong action verbs: Led, Developed, Implemented, Designed, Optimized, etc.
- If JD requires something not in evidence, add to need_info

Return JSON with: education[], experience[], skills[], need_info[]"""
