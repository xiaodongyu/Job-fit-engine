# Revise Cluster Percentage Derivation to Match Ground Truth

## Current vs ground truth

**Current derivation** ([scripts/qa_helpers.py](../scripts/qa_helpers.py) `cluster_distribution_from_response`): We use **item counts per cluster**. Each skill/experience can be in multiple clusters; we add the same item to each cluster's `items` list. We then use `len(items)` per cluster and normalize by the **sum of all cluster sizes**. So we use **fraction of (item, cluster) pairs** per cluster. Items in more clusters contribute more to the total, which can distort the distribution.

**Ground truth** (e.g. [Resume_1_MLE_Enriched.txt](../test_fixtures/quant_cross_functional_role_fit_benchmark/Resume_1_MLE_Enriched.txt), [quant readme](../test_fixtures/quant_cross_functional_role_fit_benchmark/readme.md)): "Role-fit" distribution over MLE/DS/SWE/QR/QD that sums to 100%. Conceptually, each **resume item** (skill/experience) contributes to role fit, and that contribution is spread across the roles it applies to.

**Revised rule (equal-split per item):** Each skill/experience has total weight **1.0**. Split it **evenly** across all clusters it is assigned to. Sum weights per cluster, then normalize to a distribution. So an item in 2 clusters adds 0.5 to each; an item in 1 cluster adds 1.0. Each resume item contributes equally overall; multi-label no longer over-weights.

---

## Implementation

### 1. Compute `role_fit_distribution` in `run_clustering`

**File:** [backend/rag.py](../backend/rag.py)

- In `run_clustering`, after building `assignments` and **before** building `ClusteredGroup`s, compute a `role_fit_distribution: dict[str, float]` over `MLE|DS|SWE|QR|QD`:
  - Initialize `weights = {c: 0.0 for c in ["MLE","DS","SWE","QR","QD"]}`.
  - For each `a` in `assignments`: `clusters_list = a.get("clusters", [])` filtered to valid cluster ids. If empty, skip. Else `w = 1.0 / len(clusters_list)`, and for each `cid` in `clusters_list` do `weights[cid] += w`.
  - Normalize: `total = sum(weights.values())`; if `total > 0`, divide each `weights[c]` by `total`.
- **Return** `(list[ClusteredGroup], role_fit_distribution)` from `run_clustering` (keep existing cluster-building logic unchanged).

### 2. Store and expose `role_fit_distribution`

**File:** [backend/rag.py](../backend/rag.py)

- In `_run_full_pipeline`, where we call `run_clustering` and then `save_clusters`:
  - Unpack `clusters, role_fit_distribution = run_clustering(...)`.
  - Add `"role_fit_distribution": role_fit_distribution` to the dict passed to `save_clusters` (so it's stored in `clusters.json`).

**File:** [backend/models.py](../backend/models.py)

- Extend `ClusterResponse` with `role_fit_distribution: Optional[dict[str, float]] = None`.

**File:** [backend/main.py](../backend/main.py)

- In `cluster_experience`, when loading from `rag.load_clusters` and returning `ClusterResponse`, pass `role_fit_distribution=data.get("role_fit_distribution")` into the response. Fallback cluster (stickers/paste) does not have it; leave it `None`.

### 3. Use `role_fit_distribution` when present

**File:** [scripts/qa_helpers.py](../scripts/qa_helpers.py)

- In `cluster_distribution_from_response`:
  - If the response has `role_fit_distribution` (and it's a non-empty dict), return that, normalized to the same keys as `CLUSTERS` (ensure all five clusters exist, missing → 0).
  - Otherwise, keep the existing item-count-based derivation (for fallback / "All Experiences" or older stored data).

### 4. Test script and QA

- [scripts/test_resume_only_clustering.py](../scripts/test_resume_only_clustering.py) and [scripts/run_qa.py](../scripts/run_qa.py) both use `cluster_distribution_from_response` (or equivalent). No changes needed there; they will automatically use the new derivation when the API returns `role_fit_distribution`.

### 5. Backward compatibility

- Old `clusters.json` files without `role_fit_distribution`: we fall back to item-count derivation in `cluster_distribution_from_response`. No migration required.
- Fallback cluster (no extraction): we never have `role_fit_distribution`; we continue to use item-count (or single-cluster) logic.

---

## Summary of edits

| File | Change |
|------|--------|
| `backend/rag.py` | Compute `role_fit_distribution` in `run_clustering` (equal-split); return it; store it in `save_clusters` payload. |
| `backend/models.py` | Add `role_fit_distribution: Optional[dict[str, float]] = None` to `ClusterResponse`. |
| `backend/main.py` | Pass `role_fit_distribution` from loaded clusters into `ClusterResponse`. |
| `scripts/qa_helpers.py` | Prefer `role_fit_distribution` in `cluster_distribution_from_response` when present; else keep current logic. |

---

## Verification

- Re-run resume-only clustering test: `python scripts/test_resume_only_clustering.py -r test_fixtures/quant_cross_functional_role_fit_benchmark/Resume_1_MLE_Enriched.txt`. Percentages should now follow the equal-split rule and may align better with ground truth (e.g. MLE 55%, SWE 25%, DS 15%) than the previous item-count derivation.
- Run batch QA (Phase 1) and confirm L1 vs `ground_truth_before` uses the new distribution.
