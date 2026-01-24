I generated the **QA manifest JSON** that pairs each resume with **2–3 expected best-fit JDs**, including:

* Expected **overall match score** (0–1)
* Expected **per-cluster match scores** (coverage of JD demand by resume capability)
* Metadata links to the **JD PDF filenames**
* Explicit **tolerances** for automated regression testing

**Download:**
[qa_manifest_resume_jd_pairings.zip](sandbox:/mnt/data/qa_manifest_resume_jd_pairings.zip)

**Contents:**

* `qa_manifest_resume_jd_pairings.json`
* `README.txt` (scoring method + recommended QA assertions)

If you want the manifest to also incorporate the **add-on materials** (before/after pairing expectations), I can extend this to a *two-phase* pairing spec: `resume_only` vs `resume_plus_addon` with expected score deltas per JD.
