"""
QA helpers for the test plan in test_fixtures/batch-qa-testing-plan.md.
Path resolution, JD PDF parsing, API client, cluster distribution, L1/delta metrics.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Project root (parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_ROOT = PROJECT_ROOT / "test_fixtures"

BENCHMARK_DIR = FIXTURES_ROOT / "resume_cross_functional_role"
ADDONS_DIR = FIXTURES_ROOT / "additional_materials_complement_resumes"
JDS_DIR = FIXTURES_ROOT / "jd_senior_us_mixed_roles"
MAPPING_DIR = FIXTURES_ROOT / "qa_manifest_mapping"
PAIRINGS_DIR = FIXTURES_ROOT / "qa_manifest_resume_jd_pairings"
TWO_PHASE_DIR = FIXTURES_ROOT / "qa_manifest_resume_jd_pairings_two_phase"
TWO_PHASE_PASSFAIL_DIR = FIXTURES_ROOT / "qa_manifest_resume_jd_pairings_two_phase_passfail"

CLUSTERS = ["MLE", "DS", "SWE", "QR", "QD"]


def resolve_resume(resume_file: str) -> Path:
    return BENCHMARK_DIR / resume_file


def resolve_addon(addon_file: str) -> Path:
    return ADDONS_DIR / addon_file


def resolve_jd_pdf(jd_pdf: str) -> Path:
    return JDS_DIR / jd_pdf


def parse_jd_pdf(path: Path) -> str:
    """Extract text from JD PDF. Uses PyMuPDF (fitz)."""
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PyMuPDF (fitz) required for JD PDF parsing. pip install PyMuPDF")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    doc = fitz.open(path)
    parts = []
    for page in doc:
        t = page.get_text()
        if t and t.strip():
            parts.append(t)
    doc.close()
    return "\n".join(parts) if parts else ""


def load_manifest_mapping() -> dict[str, Any]:
    p = MAPPING_DIR / "qa_manifest.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_manifest_pairings() -> dict[str, Any]:
    p = PAIRINGS_DIR / "qa_manifest_resume_jd_pairings.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_manifest_two_phase_passfail() -> dict[str, Any]:
    p = TWO_PHASE_PASSFAIL_DIR / "qa_manifest_resume_jd_pairings_two_phase.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# --- API client ---

def _base(base_url: str) -> str:
    return base_url.rstrip("/")


def upload_resume(base_url: str, session_id: str, text: str) -> dict[str, Any]:
    r = requests.post(
        f"{_base(base_url)}/resume/upload/json",
        json={"session_id": session_id, "text": text},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def poll_until_ready(
    base_url: str, upload_id: str, poll_interval: float = 2.0, max_wait: float = 180.0
) -> tuple[str, str]:
    """Poll /resume/status until ready or error. Returns (status, detail)."""
    start = time.monotonic()
    detail = ""
    while (time.monotonic() - start) < max_wait:
        r = requests.get(f"{_base(base_url)}/resume/status", params={"upload_id": upload_id}, timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data.get("status", "")
        detail = data.get("detail", "") or ""
        if status == "ready":
            return "ready", ""
        if status == "error":
            return "error", detail
        time.sleep(poll_interval)
    return "timeout", ""


def add_materials(base_url: str, session_id: str, text: str) -> dict[str, Any]:
    r = requests.post(
        f"{_base(base_url)}/resume/materials/add/json",
        json={"session_id": session_id, "text": text},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def cluster_experience(base_url: str, session_id: str) -> dict[str, Any]:
    r = requests.post(
        f"{_base(base_url)}/experience/cluster",
        json={"session_id": session_id, "items": [], "resume_text": None},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def match_by_cluster(base_url: str, session_id: str, jd_text: str, debug: bool = False) -> dict[str, Any]:
    r = requests.post(
        f"{_base(base_url)}/analyze/match-by-cluster",
        json={
            "session_id": session_id,
            "use_curated_jd": False,
            "jd_text": jd_text,
            "debug": debug,
        },
        headers={"Content-Type": "application/json"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def health_check(base_url: str) -> bool:
    try:
        r = requests.get(f"{_base(base_url)}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# --- Cluster distribution & L1 ---

def cluster_distribution_from_response(cluster_response: dict[str, Any]) -> dict[str, float]:
    """
    Build normalized distribution over MLE/DS/SWE/QR/QD from /experience/cluster response.
    Prefers role_fit_distribution (equal-split) when present; else uses item counts per cluster.
    """
    rfd = cluster_response.get("role_fit_distribution")
    if isinstance(rfd, dict) and rfd:
        dist = {c: 0.0 for c in CLUSTERS}
        for k, v in rfd.items():
            k = str(k).upper()
            if k in dist:
                dist[k] = float(v)
        return dist

    dist = {c: 0.0 for c in CLUSTERS}
    clusters = cluster_response.get("clusters") or []
    total = 0
    for g in clusters:
        label = (g.get("cluster_label") or g.get("cluster_id") or "").upper()
        if label in dist:
            n = len(g.get("items") or [])
            dist[label] = float(n)
            total += n
    if total > 0:
        for k in dist:
            dist[k] /= total
    return dist


def l1_error(p: dict[str, float], q: dict[str, float]) -> float:
    """L1 distance between two distributions over same keys."""
    keys = set(p) | set(q)
    return sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def normalize_ground_truth(gt: dict[str, float]) -> dict[str, float]:
    """Ensure GT has all clusters; missing => 0."""
    out = {c: 0.0 for c in CLUSTERS}
    for k, v in gt.items():
        k = str(k).upper()
        if k in out:
            out[k] = float(v)
    return out


def primary_cluster_l1(pred: dict[str, float], gt: dict[str, float]) -> float:
    """L1 restricted to the primary (max) cluster in ground truth."""
    gt_n = normalize_ground_truth(gt)
    primary = max(gt_n, key=gt_n.get)
    return abs((pred.get(primary) or 0.0) - (gt_n.get(primary) or 0.0))


def delta_direction(actual_delta: float, expected_direction: str, deadband: float = 0.01) -> bool:
    """Check if actual delta matches expected direction (+, -, ~)."""
    if expected_direction == "+":
        return actual_delta >= -deadband
    if expected_direction == "-":
        return actual_delta <= deadband
    if expected_direction in ("~", "="):
        return -deadband <= actual_delta <= deadband
    return True
