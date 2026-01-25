# QA Report

**Base URL:** http://localhost:8000
**Phases:** [1, 3]

## Phase 1 (Resume-only clustering)

- **R1_MLE_Enriched** (qa_R1_MLE_Enriched_resume_only): L1 overall=0.3230, primary=0.0343 — PASS
- **R2_DS_Enriched** (qa_R2_DS_Enriched_resume_only): L1 overall=0.3389, primary=0.1694 — PASS
- **R3_SWE_Enriched** (qa_R3_SWE_Enriched_resume_only): L1 overall=0.2582, primary=0.0127 — PASS
- **R4_QR_Enriched** (qa_R4_QR_Enriched_resume_only): L1 overall=0.2815, primary=0.0463 — PASS
- **R5_QD_Switcher** (qa_R5_QD_Switcher_resume_only): L1 overall=0.3043, primary=0.0615 — PASS

## Phase 2 (Augmentation)


## Phase 3 (Resume–JD match, resume-only)

- **R1_MLE_Enriched**: FAIL
  - JD_MLE_01_Amazon_TrainingInfra: overall=0.3 (exp 0.85) — fail
    cluster_matches: MLE 0.650, DS 0.200, SWE 0.150, QD 0.000
  - JD_MLE_02_Amazon_GenAIIC: overall=0.125 (exp 0.8) — fail
    cluster_matches: MLE 0.500, DS 0.000, SWE 0.000, QD 0.000
  - JD_SWE_02_Amazon_Neuron_DistributedTraining: overall=0.2 (exp 0.55) — fail
    cluster_matches: MLE 0.400, DS 0.000, SWE 0.200, QD 0.000
- **R2_DS_Enriched**: FAIL
  - JD_DS_02_Microsoft_SeniorDataScientist_MediaOptimization: overall=0.45 (exp 0.85) — fail
    cluster_matches: MLE 0.300, DS 0.750, SWE 0.050, QD 0.000, QR 0.000
  - JD_DS_01_Amazon_SeniorDataScientist_DML: overall=0.3 (exp 0.8) — fail
    cluster_matches: MLE 0.300, DS 0.700, SWE 0.100, QR 0.000, QD 0.000
  - JD_MLE_01_Amazon_TrainingInfra: overall=0.27 (exp 0.4) — fail
    cluster_matches: MLE 0.200, DS 0.500, SWE 0.150, QD 0.000, QR 0.100
- **R3_SWE_Enriched**: FAIL
  - JD_SWE_02_Amazon_Neuron_DistributedTraining: overall=0.31 (exp 0.8) — fail
    cluster_matches: MLE 0.200, DS 0.000, SWE 0.700, QR 0.000, QD 0.150
  - JD_SWE_01_Google_DistributedCloud: overall=0.3 (exp 0.75) — fail
    cluster_matches: MLE 0.300, DS 0.000, SWE 0.700, QR 0.000, QD 0.000
  - JD_QD_01_TwoSigma_QuantSoftwareEngineer: overall=0.2 (exp 0.5) — fail
    cluster_matches: MLE 0.100, DS 0.000, SWE 0.400, QR 0.100, QD 0.200
- **R4_QR_Enriched**: FAIL
  - JD_QR_01_TwoSigma_QuantResearcher_Experienced: overall=0.3 (exp 0.85) — fail
    cluster_matches: MLE 0.000, DS 0.200, SWE 0.000, QR 0.650, QD 0.000
  - JD_QR_02_Citadel_QuantResearch_Profile: overall=0.3 (exp 0.8) — fail
    cluster_matches: MLE 0.000, DS 0.200, SWE 0.000, QR 0.600, QD 0.100
  - JD_QD_01_TwoSigma_QuantSoftwareEngineer: overall=0.26 (exp 0.35) — fail
    cluster_matches: MLE 0.000, DS 0.200, SWE 0.000, QR 0.550, QD 0.000
- **R5_QD_Switcher**: FAIL
  - JD_QD_01_TwoSigma_QuantSoftwareEngineer: overall=0.3 (exp 0.85) — fail
    cluster_matches: DS 0.000, SWE 0.200, QR 0.200, QD 0.600
  - JD_QD_02_Citadel_QuantDeveloper_Profile: overall=0.35 (exp 0.85) — fail
    cluster_matches: DS 0.000, SWE 0.200, QR 0.000, QD 0.600
  - JD_QR_01_TwoSigma_QuantResearcher_Experienced: overall=0.25 (exp 0.4) — fail
    cluster_matches: DS 0.000, SWE 0.100, QR 0.200, QD 0.400

## Phase 4 (Two-phase match)


## Phase 5 (Pass/fail rules)
