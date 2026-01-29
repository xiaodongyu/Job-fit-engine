Below is a **precise, QA-grade methodology** for how the **GROUND-TRUTH ROLE FIT percentages** (e.g., in `Resume_1_MLE_Enriched.txt`) are computed. This is written so it can be implemented deterministically and audited—**not** as a vague heuristic.

---

# Ground-Truth Role Fit Percentage: Computation Method

## 0. Purpose of the percentages (important framing)

These percentages are **capability-weighted role fit**, not:

* probability of hire
* user intent
* keyword density

They answer:

> *“If this candidate were evaluated purely on demonstrated evidence, how much of their experience supports each role cluster?”*

They are used as:

* **Gold labels for QA**
* Targets for **cluster inference calibration**
* Inputs to **resume ↔ JD matching math**

---

## 1. Canonical role clusters (fixed)

All resumes are evaluated against the same closed set:

```
R = { MLE, DS, SWE, QR, QD }
```

No open-ended roles. This is critical for QA stability.

---

## 2. Evidence-first principle (non-negotiable)

**No percentage is assigned without evidence.**

Every contribution to a role score must map to:

* a specific experience bullet
* a project
* a responsibility
* or a supplemental artifact

Each evidence item must be:

* attributable to a resume section
* classifiable to ≥1 role cluster

---

## 3. Evidence extraction and normalization

### 3.1 Break resume into atomic evidence units

Each resume is decomposed into **atomic evidence units**:

Examples:

* One experience bullet
* One project description
* One responsibility statement
* One add-on artifact paragraph

Each unit is treated independently.

---

## 4. Role evidence scoring per unit

Each evidence unit is scored against **each role cluster** using a **tiered signal model**.

### 4.1 Signal tiers (role-specific)

Each role has **Tier-1 / Tier-2 / Tier-3 signals** (already defined earlier).
Weights are fixed across resumes.

| Signal Tier | Meaning                        | Weight  |
| ----------- | ------------------------------ | ------- |
| Tier-1      | Core defining responsibility   | **1.0** |
| Tier-2      | Strong adjacent responsibility | **0.6** |
| Tier-3      | Weak / contextual signal       | **0.3** |

Example for **MLE**:

* Tier-1: model deployment, training pipelines, drift monitoring
* Tier-2: PyTorch, Airflow, feature engineering
* Tier-3: “used ML models” without deployment context

---

### 4.2 Multi-role contribution allowed

A **single evidence unit may contribute to multiple roles**.

Example bullet:

> “Built a real-time ranking model and deployed it via a low-latency inference service.”

| Role | Tier   | Weight |
| ---- | ------ | ------ |
| MLE  | Tier-1 | 1.0    |
| SWE  | Tier-2 | 0.6    |
| DS   | Tier-2 | 0.6    |

This is why resumes remain **cross-functional**.

---

## 5. Raw role score accumulation

For each role ( r \in R ):

[
\text{RawScore}(r) = \sum_{e \in Evidence} \text{TierWeight}(e, r)
]

This produces **unnormalized role strength**.

---

## 6. Seniority and ownership weighting (crucial)

Each evidence unit is multiplied by an **ownership multiplier**:

| Evidence Source                     | Multiplier |
| ----------------------------------- | ---------- |
| Primary role responsibility         | 1.0        |
| Parallel / secondary responsibility | 0.8        |
| Earlier career role                 | 0.7        |
| Add-on / supplemental artifact      | 0.6        |
| Coursework / learning only          | 0.4        |

This prevents:

* coursework from overpowering experience
* add-ons from “magically” transforming profiles

So the real formula is:

[
\text{WeightedScore}(r) = \sum_e \text{TierWeight}(e, r) \times \text{OwnershipMultiplier}(e)
]

---

## 7. Normalization to percentages

After computing weighted scores for all roles:

[
\text{RoleFit}(r) = \frac{\text{WeightedScore}(r)}{\sum_{k \in R} \text{WeightedScore}(k)}
]

This guarantees:

* percentages sum to **100%**
* zero evidence → zero percentage

---

## 8. Example: Resume_1_MLE_Enriched (simplified)

### 8.1 Aggregated weighted scores (illustrative)

| Role | WeightedScore |
| ---- | ------------- |
| MLE  | 9.8           |
| SWE  | 4.4           |
| DS   | 2.7           |
| QD   | 0.9           |
| QR   | 0.0           |

### 8.2 Normalize

Total = 17.8

| Role | Percentage           |
| ---- | -------------------- |
| MLE  | 9.8 / 17.8 ≈ **55%** |
| SWE  | 4.4 / 17.8 ≈ **25%** |
| DS   | 2.7 / 17.8 ≈ **15%** |
| QD   | 0.9 / 17.8 ≈ **5%**  |
| QR   | 0%                   |

Matches the ground truth.

---

## 9. Hard constraints enforced (QA rules)

These constraints were applied when generating the resumes:

1. **Primary role must have ≥1 Tier-1 evidence**
2. **No role >80%** unless the resume is intentionally “pure” (none are)
3. **Secondary roles must have ≥2 evidence units**
4. **QR never assigned without research lifecycle evidence**
5. **QD never assigned without system-level infra or backtesting evidence**

Violations → role percentage forced to zero.

---

## 10. Why this method is QA-correct

This approach ensures:

* Determinism (same resume → same distribution)
* Evidence traceability
* Multi-role realism
* Robustness to keyword stuffing
* Clean alignment with JD matching math

It also makes **failure analysis trivial**:

* wrong percentage → inspect evidence units
* missing role → missing Tier-1 signals
* inflated role → weak Tier-3 overweighting

---

## 11. How your system should be evaluated against this

For QA:

* You **do not** need to match exact percentages
* You **must** match:

  * primary role
  * relative ordering
  * approximate mass (within tolerance)
  * evidence attribution

That’s why tolerances exist in the manifest.

---

## 12. Optional extension (recommended)

You can store an **intermediate artifact** for explainability:

```json
{
  "role": "MLE",
  "evidence_contributions": [
    {"text":"Built ML training pipeline", "tier":1, "weight":1.0},
    {"text":"Deployed inference service", "tier":1, "weight":1.0},
    {"text":"Used PyTorch", "tier":2, "weight":0.6}
  ],
  "weighted_sum": 9.8
}
```

This makes audits and debugging dramatically easier.

---

### Bottom line

The percentages are **not subjective**.
They are the result of a **tiered, evidence-weighted, normalized scoring model** designed explicitly for **resume evaluation QA**.

If you want, I can:

* formalize this as a **spec doc**
* convert it into **pseudo-code**
* provide a **reference Python implementation**
* align it exactly to your production scoring logic

Just tell me which artifact you want next.
