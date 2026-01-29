QA Manifest: Resume ↔ JD Pairings

File: qa_manifest_resume_jd_pairings.json

What this is:
- For each synthetic resume in resume_cross_functional_role.zip, this manifest lists 2–3 expected best-fit job descriptions (JDs)
  from jd_senior_us_mixed_roles.zip.
- Includes target overall match scores and per-cluster match scores to support automated regression testing.

How scores are computed (deterministic baseline):
- overall_match = 1 - L1_distance(resume_cluster_fit, jd_cluster_demand) / 2
- per_cluster_match (for each cluster where JD demand > 0) = min(resume, jd) / jd
  (interpretable as coverage of JD demand by resume capability for that cluster)

Recommended QA assertions:
1) The top-ranked JD for each resume should be within overall_match_abs_error of expected_overall_match.
2) Cluster match estimates should be within per_cluster_match_abs_error, especially for the JD's primary cluster.
3) Evidence:
   - Your system must provide >=2 evidence items for each cluster it claims contributes meaningfully to the match.
   - Evidence must be verbatim spans, with source attribution to resume or supplemental materials.

Tolerances:
- overall_match_abs_error: 0.08
- per_cluster_match_abs_error: 0.12

Note:
- These are QA targets for a benchmark; your production scoring model may differ.
  If you use a different scoring formulation, keep pairings and relative ranking stable and map to your score space.
