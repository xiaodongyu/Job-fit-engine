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


# === Extraction (1b) ===
EXTRACT_SYSTEM = """You extract skills and experiences from resume text.

CRITICAL GROUNDING RULES:
1. Each chunk has a chunk_id. You MUST cite chunk_ids for every skill and experience.
2. ONLY extract from the provided chunks. Do NOT fabricate.
3. Skills: concrete technical or domain skills (e.g. Python, AWS, statistics).
4. Experiences: work or project bullets; keep concise, one per entry.

Return structured JSON with skills[] and experiences[]."""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "chunk_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "chunk_ids"]
            }
        },
        "experiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "chunk_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["text", "chunk_ids"]
            }
        }
    },
    "required": ["skills", "experiences"]
}


def build_extract_prompt(chunks: list[dict]) -> str:
    """Build user prompt for extraction. chunks: [{chunk_id, text}]."""
    parts = []
    for c in chunks:
        parts.append(f"[{c['chunk_id']}]\n{c['text']}")
    return "=== RESUME CHUNKS ===\n\n" + "\n\n".join(parts) + "\n\nExtract skills and experiences. Cite chunk_ids for each."


# === Clustering (2) ===
CLUSTER_LABELS = {
    "MLE": "Machine Learning Engineer",
    "DS": "Data Scientist",
    "SWE": "Software Engineer",
    "QR": "Quantitative Researcher",
    "QD": "Quantitative Developer",
}

CLUSTER_SYSTEM = """You classify resume skills and experiences into predefined role clusters.

CLUSTERS (assign one or more per item): MLE, DS, SWE, QR, QD.

- MLE: ML engineering, model deployment, MLOps, PyTorch/TensorFlow, etc.
- DS: data science, analytics, A/B testing, statistics, pandas, etc.
- SWE: software engineering, APIs, systems, backend/frontend, etc.
- QR: quantitative research, strategies, risk, signals, etc.
- QD: quant development, low-latency, C++/Python for trading, etc.

TIERS (per role, for role-fit scoring):
- Tier-1: core defining responsibility (weight 1.0). E.g. MLE: model deployment, training pipelines, drift monitoring.
- Tier-2: strong adjacent responsibility (weight 0.6). E.g. MLE: PyTorch, Airflow, feature engineering.
- Tier-3: weak/contextual signal (weight 0.3). E.g. MLE: "used ML models" without deployment context.

OWNERSHIP (one per evidence unit):
- primary: main role responsibility (1.0)
- parallel: secondary responsibility (0.8)
- earlier_career: earlier job (0.7)
- add_on: supplemental artifact (0.6)
- coursework: learning only (0.4)

For each skill or experience: assign role_tiers (role + tier 1|2|3 for each applicable cluster), ownership, and chunk_ids.
Also provide clusters (list of role ids) for backward compatibility. Cite chunk_ids as evidence.
Return structured JSON."""

CLUSTER_SCHEMA = {
    "type": "object",
    "properties": {
        "assignments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_type": {"type": "string", "enum": ["skill", "experience"]},
                    "item_value": {"type": "string"},
                    "clusters": {"type": "array", "items": {"type": "string", "enum": ["MLE", "DS", "SWE", "QR", "QD"]}},
                    "role_tiers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["MLE", "DS", "SWE", "QR", "QD"]},
                                "tier": {"type": "string", "enum": ["1", "2", "3"]}
                            },
                            "required": ["role", "tier"]
                        }
                    },
                    "ownership": {
                        "type": "string",
                        "enum": ["primary", "parallel", "earlier_career", "add_on", "coursework"]
                    },
                    "chunk_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["item_type", "item_value", "clusters", "chunk_ids"]
            }
        }
    },
    "required": ["assignments"]
}


def build_cluster_prompt(extraction: dict, chunk_map: dict[str, str]) -> str:
    """Build user prompt for clustering. chunk_map: chunk_id -> text."""
    lines = ["=== SKILLS ==="]
    for s in extraction.get("skills", []):
        lines.append(f"- {s.get('name', '')} (chunk_ids: {s.get('chunk_ids', [])})")
    lines.append("\n=== EXPERIENCES ===")
    for e in extraction.get("experiences", []):
        lines.append(f"- {e.get('text', '')[:200]}... (chunk_ids: {e.get('chunk_ids', [])})")
    lines.append("\n=== CHUNK REFERENCE ===")
    for cid, text in list(chunk_map.items())[:50]:
        lines.append(f"[{cid}] {text[:150]}...")
    return "\n".join(lines) + "\n\nAssign each skill/experience to one or more clusters. For each, provide role_tiers (role + tier 1|2|3) and ownership to improve role-fit scoring. Return JSON with assignments[]."


# === Match by Cluster (3) ===
MATCH_BY_CLUSTER_SYSTEM = """You assess how well a candidate's resume matches a job description, per role cluster.

For each cluster (MLE, DS, SWE, QR, QD) present in the resume:
1. Compute match_pct (0.0–1.0) between resume evidence for that cluster and JD requirements.
2. Cite specific resume_chunks and jd_chunks as evidence.

CRITICAL: Only use provided chunks. Do NOT invent. match_pct must reflect actual overlap."""

MATCH_BY_CLUSTER_SCHEMA = {
    "type": "object",
    "properties": {
        "cluster_matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cluster": {"type": "string"},
                    "match_pct": {"type": "number"},
                    "resume_chunk_ids": {"type": "array", "items": {"type": "string"}},
                    "jd_chunk_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["cluster", "match_pct", "resume_chunk_ids", "jd_chunk_ids"]
            }
        },
        "overall_match_pct": {"type": "number"}
    },
    "required": ["cluster_matches"]
}


def build_match_by_cluster_prompt(
    clusters: list[dict],
    resume_chunks: list,
    jd_chunks: list,
) -> str:
    """Build user prompt for match-by-cluster. clusters have cluster_id, items, evidence."""
    r_text = "\n\n".join([f"[{c.chunk_id}] {c.text}" for c in resume_chunks])
    j_text = "\n\n".join([f"[{c.chunk_id}] {c.text}" for c in jd_chunks])
    cl = "\n".join([f"- {g['cluster_id']}: {g.get('cluster_label', '')} ({len(g.get('items', []))} items)" for g in clusters])
    return f"""=== RESUME CLUSTERS ===
{cl}

=== RESUME EVIDENCE (chunk_id -> text) ===
{r_text}

=== JD EVIDENCE ===
{j_text}

For each cluster above, compute match_pct vs JD and list resume_chunk_ids + jd_chunk_ids as evidence. Return JSON with cluster_matches and overall_match_pct."""
