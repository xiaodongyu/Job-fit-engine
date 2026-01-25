# Test fixtures for offline testing

Put your local files here when testing the backend with resume, JD, and additional materials.

## Layout

### Root-level files (ad-hoc testing)

| File | Description |
|------|-------------|
| **`resume.pdf`** | Your resume (PDF). You provide this. |
| **`resume.txt`** | Alternative: resume as plain text. |
| **`jd.txt`** | Job description (plain text). |
| **`materials.txt`** | Optional: extra context (projects, cover letter, etc.). |

Use these with [test_on_single_resume_jd.md](test_on_single_resume_jd.md) or [single-qa-test-plan.md](single-qa-test-plan.md). **Do not save real resumes here.**

### Subfolders (structured QA)

| Folder | Contents | Use |
|--------|----------|-----|
| **[resume_cross_functional_role/](resume_cross_functional_role/)** | 5 synthetic resumes (R1–R5), `Evaluation_Rubric_Role_Fit.txt`, `role_percentage_comp_method.md` | Resume-only clustering, augmentation inputs; role-fit rubric and GT percentage method |
| **[additional_materials_complement_resumes/](additional_materials_complement_resumes/)** | 5 add-ons (1 per resume) | Augmentation (Phase 2); evidence provenance checks |
| **[jd_senior_us_mixed_roles/](jd_senior_us_mixed_roles/)** | 10 JD PDFs (2 each MLE/DS/SWE/QD/QR), `jd_index.json` | Resume–JD match tests; JD metadata and cluster demand |
| **[qa_manifest_mapping/](qa_manifest_mapping/)** | `qa_manifest.json` | Ground truth before/after, deltas, evidence themes, L1 thresholds (Phase 1–2) |
| **[qa_manifest_resume_jd_pairings/](qa_manifest_resume_jd_pairings/)** | `qa_manifest_resume_jd_pairings.json` | Resume–JD pairings (resume-only); expected overall + per-cluster match (Phase 3) |
| **[qa_manifest_resume_jd_pairings_two_phase/](qa_manifest_resume_jd_pairings_two_phase/)** | `qa_manifest_resume_jd_pairings_two_phase.json` | Two-phase pairings (resume_only vs resume_plus_addon) and deltas (Phase 4) |
| **[qa_manifest_resume_jd_pairings_two_phase_passfail/](qa_manifest_resume_jd_pairings_two_phase_passfail/)** | Same JSON + `pass_fail_rule_set` | Pass/fail rules (global, phase, case-level) for automated harness (Phase 5) |

Path resolution for manifests: `resume_file` → `resume_cross_functional_role/`, `addon_file` → `additional_materials_complement_resumes/`, `jd_pdf` → `jd_senior_us_mixed_roles/`.

---

## Test methods

Three documents describe how to run tests. Choose by goal: quick smoke, ad-hoc single resume–JD, or structured batch QA.

### 1. [single-qa-test-plan.md](single-qa-test-plan.md)

**Purpose:** Smoke / sanity QA of the backend pipeline.

- **Fixtures:** Exactly `resume.txt`, `jd.txt`, `materials.txt` in this folder.
- **Flow:** Upload (resume + materials merged) → poll → **cluster experience** → **match-by-cluster** with JD. Optionally analyze/fit.
- **Upload:** JSON only (`POST /resume/upload/json` with merged text).
- **Session:** Fixed `session_id` (`single_qa_test`) for reproducibility.
- **Format:** Step-by-step curl/Python with **pass/fail** criteria per step.
- **Cluster & match:** **Required** (cluster + match-by-cluster). Analyze/fit optional.

**Use when:** You want a minimal, repeatable smoke test with explicit pass/fail checks.

---

### 2. [test_on_single_resume_jd.md](test_on_single_resume_jd.md)

**Purpose:** User-facing guide for testing with your own local files (no QA framework).

- **Fixtures:** Your `resume.pdf` / `resume.txt`, `jd.txt`, `materials.txt` (samples in this folder).
- **Flow:** Upload resume (PDF or text) → poll → **analyze/fit** (JD from file). Optional: generate resume, match-by-cluster, add-materials.
- **Upload:** PDF via form or TXT via JSON; add-materials as separate step or merged.
- **Session:** Any `session_id` (e.g. from upload response).
- **Format:** Tutorial-style curl examples; no pass/fail table.
- **Cluster & match:** **Analyze/fit** is the main path. **Match-by-cluster** is optional.

**Use when:** You want to try the backend with your own resume and JD, or run `test-offline.sh`.

---

### 3. [batch-qa-testing-plan.md](batch-qa-testing-plan.md)

**Purpose:** Structured batch QA with manifests, ground truth, and six phases.

- **Fixtures:** All subfolders above (5 resumes, 5 add-ons, 10 JDs, QA manifests).
- **Flow:** Phase 1 (resume-only clustering) → Phase 2 (augmentation) → Phase 3 (resume–JD match, resume-only) → Phase 4 (two-phase match) → Phase 5 (pass/fail harness) → Phase 6 (role-fit rubric, manual/LLM-as-judge).
- **Upload:** `POST /resume/upload/json` with text from `resume_cross_functional_role/`; add materials from `additional_materials_complement_resumes/`; JDs from `jd_senior_us_mixed_roles/`.
- **Runner:** `tests/run_qa.py` (e.g. `--phases 1,3`). Loads manifests, resolves paths, calls backend, computes L1/deltas, writes QA report to `test_results/` (`qa_report.json`, `qa_report.md`). Use `-o DIR` to change output directory.

**Use when:** You want full regression over the benchmark (clustering, augmentation, match-by-cluster, two-phase, pass/fail).

---

### Comparison

| | **single-qa-test-plan** | **test_on_single_resume_jd** | **batch-qa-testing-plan** |
|--|--------------------------|------------------------------|---------------------------|
| **Audience** | QA / dev running smoke test | Anyone testing with own files | Full regression / benchmark |
| **Fixtures** | 3 files (resume, jd, materials) | Your files or samples | All subfolders (manifests, 5 resumes, 10 JDs, etc.) |
| **Main path** | Cluster → match-by-cluster | Analyze/fit | Phases 1–6 (clustering, augmentation, match, two-phase, pass/fail, rubric) |
| **Cluster + match** | Required | Match-by-cluster optional | Required in phases 1, 3, 4 |
| **Pass/fail** | Yes, per step | No | Yes, via manifests and `run_qa.py` |
| **Automation** | Curl-based; references `test-offline.sh` for subset | `test-offline.sh` + manual curl | `run_qa.py` |

---

## Quick start

**Ad-hoc (your files):**

```bash
./tests/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt
# With materials:
./tests/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt -m test_fixtures/materials.txt
```

**Manual curl:** See [test_on_single_resume_jd.md](test_on_single_resume_jd.md).

**Smoke QA (3 files):** See [single-qa-test-plan.md](single-qa-test-plan.md).

**Batch QA (manifests + benchmark):** See [batch-qa-testing-plan.md](batch-qa-testing-plan.md) and `python tests/run_qa.py --phases 1,3`. Reports go to `test_results/` by default.
