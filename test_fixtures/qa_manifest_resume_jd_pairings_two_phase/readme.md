Yes—done. I extended the pairing manifest into a **two-phase spec** that includes:

* **resume_only** expected match scores (overall + per-cluster)
* **resume_plus_addon** expected match scores (overall + per-cluster)
* **expected score deltas** per JD (direction + numeric delta)
* Embedded references to the correct **addon file** for each resume
* Evidence requirements and augmentation assertions carried forward

**Download:**
[qa_manifest_resume_jd_pairings_two_phase.zip](sandbox:/mnt/data/qa_manifest_resume_jd_pairings_two_phase.zip)

**Contents:**

* `qa_manifest_resume_jd_pairings_two_phase.json`
* `README.txt` (how to use + scoring baseline + tolerances)

If you want, I can also add a “**pass/fail rule set**” section per case (e.g., “top JD must remain stable”, “delta must be positive for these JDs”, “primary cluster evidence must include ≥1 addon quote”), so your QA harness can run completely unattended.
