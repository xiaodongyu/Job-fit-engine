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
RESUME_GENERATE_SYSTEM = """You are a professional resume writer.

GROUNDING RULES:
- ONLY use the provided FACTS / EVIDENCE. Do NOT invent.
- If required information is missing, put it in need_info.

FORMAT RULES (must follow exactly):
- EDUCATION section: each entry is two lines:
  Line 1: School | Location
  Line 2: Degree/Field | Start–End
  Then bullets (optional)

- EXPERIENCE section: each role is two lines:
  Line 1: Company | Location
  Line 2: Title | Start–End
  Then bullets

- PROJECTS section: each project is two lines:
  Line 1: Project Name | Location (or null)
  Line 2: Role | Start–End
  Then bullets

- In bullets, highlight key skills by wrapping the skill term in **bold**.

WRITING STYLE:
- Use strong action verbs (Led, Developed, Implemented, Optimized, Designed, etc.)
- Write concise, impactful bullets
- Quantify impact when numbers are present in evidence (e.g., "increased performance by 40%")
- Tailor wording to target role and JD requirements
- Keep bullets professional and achievement-focused

Return structured JSON matching the schema."""

RESUME_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "experiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "role": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": ["string", "null"]},
                    "degree": {"type": ["string", "null"]},
                    "field": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "skills": {"type": "array", "items": {"type": "string"}},
        "need_info": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["experiences", "projects", "education", "skills", "need_info"]
}


# === Resume Structure Extraction (Input Stage) ===
RESUME_STRUCTURE_SYSTEM = """YYou are a resume parser that extracts structured sections into JSON.

OUTPUT RULES (STRICT):
- Output ONLY a single JSON object, no markdown, no commentary.
- Use ONLY keys allowed by the schema. Do not add extra keys.
- Every item must include ALL required fields; if unknown use null; arrays default to [].

SECTION TYPES:
- EDUCATION: school/university/degree/certifications.
- EXPERIENCE: jobs, internships, employed roles at a company (including research roles at a company).
- PROJECTS: personal/academic/research projects not framed as employment at a company.

BLOCK BOUNDARIES (CRITICAL):
- An EXPERIENCE block starts at the first line that contains a company-like name and location OR a clear employer header.
- A new EXPERIENCE block starts when you encounter another company header OR another title+date header not belonging to the current block.
- All bullets belong to the most recent block header until a new block starts.
- Same company with different titles/dates => separate experience blocks.

FIELD SEPARATORS:
- Lines may use " | " to separate fields (e.g., "Company | Location" or "Title | Dates").
- Extract each part into the appropriate field (company/location, title/start_date-end_date, etc.).

FIELD EXTRACTION:
- company/title/location/start_date/end_date: take from headers; keep dates as raw strings.
- bullets: copy bullet text verbatim (normalize whitespace; do not rewrite).
- skills_tags: extract ONLY explicit technologies/skills mentioned in the same block (tools, languages, frameworks, methods). No inference. If none: [].
- ownership: choose one based ONLY on evidence in the block:
  - "Individual (end-to-end)" if clearly solo/self-project or explicitly says individual.
  - "Led / mentored" if led/managed/mentored/owned delivery.
  - "Collaborated" if worked with/with seniors/with team.
  - otherwise null.

DO NOT INVENT:
- Extract only what exists in the resume text. If unclear, use null/[].

Finally: validate the JSON matches the schema before output."""

RESUME_STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "experiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                    "skills_tags": {"type": "array", "items": {"type": "string"}},
                    "ownership": {"type": ["string", "null"]}
                },
                "required": ["company", "title", "location", "start_date", "end_date", "bullets", "skills_tags", "ownership"]
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "role": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                    "skills_tags": {"type": "array", "items": {"type": "string"}},
                    "ownership": {"type": ["string", "null"]}
                },
                "required": ["name", "role", "location", "start_date", "end_date", "bullets", "skills_tags", "ownership"]
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": ["string", "null"]},
                    "degree": {"type": ["string", "null"]},
                    "field": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "gpa": {"type": ["string", "null"]},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    },
    "required": ["experiences", "projects", "education"]
}


def build_resume_structure_prompt(resume_text: str) -> str:
    """Build user prompt for structured resume extraction."""
    return f"""=== RESUME TEXT ===
{resume_text}

=== TASK ===
Parse the resume into structured blocks: experiences, projects, education.

OUTPUT RULES (STRICT):
- Output ONLY valid JSON. No markdown. No explanation text.
- Match the schema exactly: include ALL required keys in every item.
- If a field is missing/unknown, set it to null. For arrays, use [].
- Do NOT add extra keys not shown in the example.

CLASSIFICATION GUIDE:
- Job/internship at a company → experiences[]
- School/university with degree → education[]
- Personal/academic projects (not employment) → projects[]

BLOCK BOUNDARIES (CRITICAL):
- Start a new experience block when you see a new company header (company + location) OR a new title+date line that clearly refers to a different role.
- Bullets belong to the most recent header until a new header begins.
- Same company with different title/dates => separate experience blocks.

GROUPING RULES:
- Each company/job = ONE experience (include all its bullet points)
- Each school = ONE education (GPA, honors, coursework go into bullets)
- Each project = ONE project (include all its bullet points)

FIELD RULES:
- Keep dates as raw strings (e.g., "Sept. 2023", "Feb. 2025").
- bullets: copy bullet text verbatim (normalize whitespace only).
- skills_tags: extract ONLY explicit tools/skills mentioned in that block (e.g., Python, Java, XGBoost). No inference. If none: [].
- ownership: set to one of:
  - "Individual (end-to-end)" if explicitly solo/self-project/individual
  - "Led / mentored" if led/managed/mentored/coordinated
  - "Collaborated" if worked with/with seniors/with team
  - otherwise null

EXAMPLE OUTPUT STRUCTURE:
{{
  "experiences": [
    {{
      "company": "Google",
      "title": "Software Engineer",
      "location": "Mountain View, CA",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "bullets": ["Led team of 5...", "Improved latency by 40%..."],
      "skills_tags": ["Python", "TensorFlow"],
      "ownership": null
    }}
  ],
  "projects": [],
  "education": [
    {{
      "school": "XXX University",
      "degree": "Master of Science",
      "field": "Computer Science",
      "location": "New York",
      "start_date": "Sept. 2022",
      "end_date": "Dec. 2024",
      "gpa": "3.96",
      "bullets": ["Chair's List 2022", "Relevant Coursework: ML, Data Analysis"]
    }}
  ]
}}

Return JSON matching the schema. Do NOT split one job/school into multiple blocks."""


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

=== FACTS / EVIDENCE (use ONLY this for content) ===
{resume_text}

=== JOB DESCRIPTION (tailor wording to these, do NOT invent facts) ===
{jd_text}

Task:
- Produce a clean, standard resume following the FORMAT RULES in the system prompt.
- Each experience/project/education block must have: company/name, title/role, location, dates, bullets.
- Ensure bullets include **bold** skills where appropriate.
- If something is missing (dates/company/title), add to need_info.

Return JSON with: experiences[], projects[], education[], skills[], need_info[]."""


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
