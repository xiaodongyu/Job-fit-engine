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
                    "company": {"type": "string", "nullable": True},
                    "title": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "role": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string", "nullable": True},
                    "degree": {"type": "string", "nullable": True},
                    "field": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
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
                    "company": {"type": "string", "nullable": True},
                    "title": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                    "skills_tags": {"type": "array", "items": {"type": "string"}},
                    "ownership": {"type": "string", "nullable": True}
                },
                "required": ["company", "title", "location", "start_date", "end_date", "bullets", "skills_tags", "ownership"]
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "role": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                    "skills_tags": {"type": "array", "items": {"type": "string"}},
                    "ownership": {"type": "string", "nullable": True}
                },
                "required": ["name", "role", "location", "start_date", "end_date", "bullets", "skills_tags", "ownership"]
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string", "nullable": True},
                    "degree": {"type": "string", "nullable": True},
                    "field": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "gpa": {"type": "string", "nullable": True},
                    "bullets": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    },
    "required": ["experiences", "projects", "education"]
}


# === Two-Pass Resume Parsing ===

# --- Pass 1: Segmentation ---
RESUME_SEGMENT_SYSTEM = """You are a resume segmenter. Your ONLY job is to split resume text into blocks.

OUTPUT RULES (STRICT):
- Output ONLY a single JSON object with a "blocks" array.
- COPY lines VERBATIM. Do NOT paraphrase, rewrite, or summarize.
- Preserve line order within each block.

SECTION DETECTION:
Detect section headers like EDUCATION, WORK EXPERIENCE, EXPERIENCE, EMPLOYMENT, PROJECTS, RELEVANT PROJECTS, SKILLS, etc.
When you see a section header, subsequent blocks belong to that section until a new header appears.

BLOCK BOUNDARIES:
- Within EDUCATION: each school/university = one block (include degree lines, GPA, coursework, honors as part of that block).
- Within EXPERIENCE/WORK EXPERIENCE/EMPLOYMENT: each company+role = one block. A block starts at a line with company name (often has location) and includes title+date lines and all bullets until the next company/role header.
- Within PROJECTS: each project = one block (project name line + role line + bullets).
- SKILLS section: treat as one block of type "other".

FIELD CLASSIFICATION WITHIN A BLOCK:
- header_lines: the first 1-2 lines that identify the block (company+location, school, project name).
- meta_lines: additional header info like title+dates, degree+dates, GPA (not bullets).
- bullet_lines: lines starting with bullet markers (-, •, *, ◦, ▪) or clearly formatted as achievements.
- raw_lines: ALL lines in the block verbatim (header + meta + bullets + anything else), preserving order.

CRITICAL:
- Do NOT merge multiple companies into one block.
- Do NOT merge multiple schools into one block.
- Do NOT split one company/school across multiple blocks.
- Include ALL text in raw_lines, even lines you're unsure about.
- Use " | " as a visual separator in text if present (from tab normalization).

Return JSON with blocks[]."""

RESUME_SEGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": ["experience", "project", "education", "other"]
                    },
                    "header_lines": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "meta_lines": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "bullet_lines": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "raw_lines": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["section", "header_lines", "meta_lines", "bullet_lines", "raw_lines"]
            }
        }
    },
    "required": ["blocks"]
}


def build_resume_segment_prompt(resume_text: str) -> str:
    """Build user prompt for Pass 1 segmentation."""
    return f"""=== RESUME TEXT ===
{resume_text}

=== TASK ===
Segment this resume into blocks. Each block is one logical unit:
- One company/role for experiences
- One school for education
- One project for projects
- Skills/other sections as single blocks

RULES:
1. COPY all lines VERBATIM into raw_lines. Do NOT rewrite.
2. Classify each block's section: experience, project, education, or other.
3. Within each block, separate header_lines, meta_lines, and bullet_lines.
4. Lines with " | " often contain multiple fields (e.g., "Company | Location").

EXAMPLE OUTPUT:
{{
  "blocks": [
    {{
      "section": "education",
      "header_lines": ["Example University | New York, USA"],
      "meta_lines": ["Master of Science, Computer Science | Sept. 2022 – Dec. 2024", "GPA: 3.90; Dean's List"],
      "bullet_lines": ["Relevant Coursework: Machine Learning, Algorithms, Data Structures."],
      "raw_lines": [
        "Example University | New York, USA",
        "Master of Science, Computer Science | Sept. 2022 – Dec. 2024",
        "GPA: 3.90; Dean's List",
        "Relevant Coursework: Machine Learning, Algorithms, Data Structures."
      ]
    }},
    {{
      "section": "experience",
      "header_lines": ["TechCorp Inc. | San Francisco, USA"],
      "meta_lines": ["Software Engineer | Jan. 2023 – Present"],
      "bullet_lines": [
        "Developed machine learning pipelines...",
        "Optimized backend services..."
      ],
      "raw_lines": [
        "TechCorp Inc. | San Francisco, USA",
        "Software Engineer | Jan. 2023 – Present",
        "Developed machine learning pipelines...",
        "Optimized backend services..."
      ]
    }}
  ]
}}

Return JSON with blocks[]. Do NOT merge multiple companies or schools into one block."""


# --- Pass 2: Mapping (blocks → final schema) ---
RESUME_MAP_SYSTEM = """You are a resume mapper. You convert segmented blocks into structured schema fields.

INPUT: A list of blocks, each with section type, header_lines, meta_lines, bullet_lines, raw_lines.

OUTPUT: The final structured resume with experiences[], projects[], education[] arrays.

MAPPING RULES:

FOR EXPERIENCE BLOCKS (section="experience"):
- company: extract from header_lines (usually the first part before " | " or on its own line).
- location: extract from header_lines (usually after " | " or second part).
- title: extract from meta_lines (job title, usually before " | " on the title/date line).
- start_date, end_date: extract from meta_lines (date range like "Feb. 2025 – Present").
- bullets: copy from bullet_lines verbatim.
- skills_tags: extract ONLY explicit technologies/tools mentioned in bullet_lines (e.g., Python, XGBoost, Java). No inference.
- ownership: set based on evidence:
  - "Led / mentored" if led/managed/mentored/coordinated
  - "Collaborated" if worked with team/seniors
  - "Individual (end-to-end)" if solo/self-project
  - null otherwise

FOR EDUCATION BLOCKS (section="education"):
- school: extract from header_lines (university/college name).
- location: extract from header_lines (after " | ").
- degree: extract from meta_lines (e.g., "Master of Arts", "Bachelor of Science").
- field: extract from meta_lines (e.g., "Statistics", "Computer Science").
- start_date, end_date: extract from meta_lines.
- gpa: extract from meta_lines or bullet_lines if present.
- bullets: include honors, coursework, achievements from bullet_lines/meta_lines.

FOR PROJECT BLOCKS (section="project"):
- name: extract from header_lines (project name).
- role: extract from meta_lines (e.g., "Self-Project", "Individual Project").
- location: extract from header_lines or meta_lines if present.
- start_date, end_date: extract from meta_lines.
- bullets: copy from bullet_lines verbatim.
- skills_tags: extract explicit technologies mentioned.
- ownership: set based on evidence (Self-Project → "Individual (end-to-end)").

CRITICAL:
- Do NOT invent fields. If not present in the block, use null.
- Do NOT split one block into multiple output items.
- Each input block = exactly one output item.
- Skip blocks with section="other" (skills sections, etc.)."""


def build_resume_map_prompt(blocks_data: dict) -> str:
    """Build user prompt for Pass 2 mapping."""
    import json
    blocks_json = json.dumps(blocks_data, indent=2, ensure_ascii=False)
    return f"""=== SEGMENTED BLOCKS ===
{blocks_json}

=== TASK ===
Map each block to the final schema:
- experience blocks → experiences[]
- education blocks → education[]
- project blocks → projects[]
- Skip "other" blocks (like skills sections).

FIELD EXTRACTION:
- Parse " | " separators to split fields (Company | Location, Title | Dates, etc.).
- Keep dates as raw strings.
- Copy bullets verbatim.
- Extract skills_tags only from explicit mentions (Python, Java, XGBoost, etc.).

EXAMPLE (how to map blocks → final schema):

Example input blocks:
{{
  "blocks": [
    {{
      "section": "experience",
      "header_lines": ["TechCorp Inc. | San Francisco, USA"],
      "meta_lines": ["Software Engineer | Jan. 2023 – Present"],
      "bullet_lines": ["Built backend services in Python.", "Deployed models with XGBoost."],
      "raw_lines": [
        "TechCorp Inc. | San Francisco, USA",
        "Software Engineer | Jan. 2023 – Present",
        "Built backend services in Python.",
        "Deployed models with XGBoost."
      ]
    }},
    {{
      "section": "education",
      "header_lines": ["Example University | New York, USA"],
      "meta_lines": ["Master of Science, Computer Science | Sept. 2022 – Dec. 2024", "GPA: 3.90"],
      "bullet_lines": ["Relevant Coursework: Machine Learning, Algorithms."],
      "raw_lines": [
        "Example University | New York, USA",
        "Master of Science, Computer Science | Sept. 2022 – Dec. 2024",
        "GPA: 3.90",
        "Relevant Coursework: Machine Learning, Algorithms."
      ]
    }},
    {{
      "section": "project",
      "header_lines": ["Portfolio Optimizer | Remote"],
      "meta_lines": ["Self-Project | Jan. 2026"],
      "bullet_lines": ["Implemented mean-variance optimization in Python."],
      "raw_lines": [
        "Portfolio Optimizer | Remote",
        "Self-Project | Jan. 2026",
        "Implemented mean-variance optimization in Python."
      ]
    }}
  ]
}}

Example target JSON output:
{{
  "experiences": [
    {{
      "company": "TechCorp Inc.",
      "title": "Software Engineer",
      "location": "San Francisco, USA",
      "start_date": "Jan. 2023",
      "end_date": "Present",
      "bullets": ["Built backend services in Python.", "Deployed models with XGBoost."],
      "skills_tags": ["Python", "XGBoost"],
      "ownership": null
    }}
  ],
  "projects": [
    {{
      "name": "Portfolio Optimizer",
      "role": "Self-Project",
      "location": "Remote",
      "start_date": "Jan. 2026",
      "end_date": null,
      "bullets": ["Implemented mean-variance optimization in Python."],
      "skills_tags": ["Python"],
      "ownership": "Individual (end-to-end)"
    }}
  ],
  "education": [
    {{
      "school": "Example University",
      "degree": "Master of Science",
      "field": "Computer Science",
      "location": "New York, USA",
      "start_date": "Sept. 2022",
      "end_date": "Dec. 2024",
      "gpa": "3.90",
      "bullets": ["Relevant Coursework: Machine Learning, Algorithms."]
    }}
  ]
}}

OUTPUT SCHEMA:
{{
  "experiences": [
    {{
      "company": "...",
      "title": "...",
      "location": "...",
      "start_date": "...",
      "end_date": "...",
      "bullets": ["..."],
      "skills_tags": ["..."],
      "ownership": ["..."]
    }}
  ],
  "projects": [...],
  "education": [
    {{
      "school": "...",
      "degree": "...",
      "field": "...",
      "location": "...",
      "start_date": "...",
      "end_date": "...",
      "gpa": "...",
      "bullets": ["..."]
    }}
  ]
}}

Return JSON matching the schema. Each input block = exactly one output item."""


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
