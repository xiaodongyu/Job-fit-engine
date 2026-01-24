Added. I updated the two-phase pairing manifest to include a **pass/fail rule set** with:

* **Global rules** (schema validity, evidence count, verbatim evidence with attribution, ranking stability)
* **Phase rules** for `resume_only` and `resume_plus_addon` (score tolerances, delta direction + tolerance, addon evidence requirement)
* **Case-level overrides** per resume (expected top-1 JD per phase; list of JDs expected to have positive deltas)

**Download:**
[qa_manifest_resume_jd_pairings_two_phase_passfail.zip](sandbox:/mnt/data/qa_manifest_resume_jd_pairings_two_phase_passfail.zip)

Contents:

* `qa_manifest_resume_jd_pairings_two_phase.json` (now includes `pass_fail_rule_set` + `pass_fail_rule_set_overrides`)
* `README.txt` (updated with harness guidance and rule evaluation order)
