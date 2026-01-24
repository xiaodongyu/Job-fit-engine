QA Manifest (qa_manifest.json)

This manifest maps each resume to its corresponding supplemental add-on material and defines:
- Ground-truth role-fit distributions (before)
- Expected augmentation deltas and a target post-augmentation distribution (after)
- Required evidence themes and concrete QA assertions

Recommended QA flow per test_case:
1) Run clustering on resume_file only; compare predicted distribution to ground_truth_before.
2) Run clustering on (resume_file + addon_file); compare distribution to ground_truth_after_target and delta expectations.
3) Validate evidence:
   - >=2 evidence items per predicted cluster
   - quotes are verbatim spans from source text
   - each evidence item includes source attribution: resume vs addon
4) If using JD matching, additionally verify that per-cluster matches track JD demand distribution.

Notes:
- ground_truth_after_target is a *target* distribution for QA; allow tolerance (see global_thresholds).
- expected_delta.directional uses:
  '+' increase, '-' decrease, '~' roughly unchanged.