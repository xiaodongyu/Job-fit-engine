# Test fixtures for offline testing

Put your local files here when testing the backend with resume, JD, and additional materials.

## Layout

| File | Description |
|------|-------------|
| **`resume.pdf`** | Your resume (PDF). You provide this. |
| **`resume.txt`** | Alternative: resume as plain text. |
| **`jd.txt`** | Job description (plain text). |
| **`materials.txt`** | Optional: extra context (projects, cover letter, etc.). |

## Usage

**Automated script (from project root):**

```bash
# Resume PDF + JD (specify paths with -r / --resume and -j / --jd)
./scripts/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt

# With additional materials (-m / --materials)
./scripts/test-offline.sh -r test_fixtures/resume.pdf -j test_fixtures/jd.txt -m test_fixtures/materials.txt

# Resume as text
./scripts/test-offline.sh --resume test_fixtures/resume.txt --jd test_fixtures/jd.txt
```

**Manual curl:** use `test_fixtures/resume.pdf`, `test_fixtures/jd.txt`, etc. in the examples in [docs/testing-offline.md](docs/testing-offline.md).

## Samples

- `jd.txt` – sample job description (replace with your own).
- `materials.txt` – optional; add your extra content or leave as-is.

Real `resume.pdf` / `resume.txt` are gitignored so they are not committed.

## QA testing plan

For structured QA using resumes, JDs, additional materials, and QA manifests (ground truth, rules, pass/fail), see [qa-testing-plan.md](qa-testing-plan.md). It covers fixture layout, test phases (clustering, augmentation, resume–JD match, two-phase, pass/fail harness, role-fit rubric), and implementation notes.

**Single-fixture smoke test:** To run QA using only `resume.txt`, `jd.txt`, and `materials.txt` in this folder, see [single-qa-test-plan.md](single-qa-test-plan.md).
