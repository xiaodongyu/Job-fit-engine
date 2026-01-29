Two-Phase QA Pairing Manifest

File: qa_manifest_resume_jd_pairings_two_phase.json

Purpose
- Provides expected best-fit JD pairings for each resume under two conditions:
  (1) resume_only
  (2) resume_plus_addon (resume + supplemental material)

How to use
1) Run your pipeline on resume_only; compare predicted overall/cluster match to 'resume_only' expectations.
2) Run your pipeline on resume_plus_addon; compare to 'resume_plus_addon' expectations.
3) Validate delta behavior:
   - expected_delta.overall_match indicates the target change due to augmentation.
   - direction '+' means match should increase meaningfully; '~' means stable; '-' means decrease.

Scoring baseline (for QA targets)
- overall_match = 1 - L1_distance(resume_cluster_fit, jd_cluster_demand) / 2
- per_cluster_match = min(resume, jd) / jd for jd>0 (coverage)

Tolerances
- overall_match_abs_error: 0.08
- per_cluster_match_abs_error: 0.12
- delta_overall_match_abs_error: 0.06

Evidence requirements
- For any predicted cluster contributing to the match, provide >=2 evidence items.
- Evidence must be verbatim spans with source attribution (resume vs addon).
- Post-augmentation, at least some evidence should come from addon where it introduces Tier-1 signals.

Notes
- These are deterministic QA targets. If your production score differs, keep rankings and delta directions stable and map to your score space.


Pass/Fail Rule Set
- The manifest includes pass_fail_rule_set with:
  - global_rules: apply to all cases/phases
  - phase_rules: apply to resume_only and resume_plus_addon phases
  - pass_fail_rule_set_overrides per case (expected top-1 and positive-delta JDs)

Suggested harness behavior
- Evaluate global_rules first (fail-fast on severity=fail).
- Evaluate phase_rules next.
- Apply case overrides at the end.
- Report a summary per case: PASS / FAIL / PASS_WITH_WARNINGS (warn-only issues).
