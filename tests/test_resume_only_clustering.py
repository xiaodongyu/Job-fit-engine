#!/usr/bin/env python3
"""
Resume-only clustering test: upload a resume, run /experience/cluster, output cluster assignment and percentage.

Usage:
  python tests/test_resume_only_clustering.py [--resume PATH] [--base-url URL]

Backend must be running. Default resume: test_fixtures/resume.txt. Default base-url: http://localhost:8000.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PROJECT_ROOT = _TESTS.parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from qa_helpers import (
    CLUSTERS,
    cluster_distribution_from_response,
    cluster_experience,
    health_check,
    poll_until_ready,
    upload_resume,
)


def _resolve_resume_path(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return p


def run(base_url: str, resume_path: Path) -> int:
    base_url = base_url.rstrip("/")
    if not health_check(base_url):
        print("Backend not reachable at", base_url, "- start it first.")
        return 1

    if not resume_path.exists():
        print("Resume not found:", resume_path)
        return 1

    text = resume_path.read_text(encoding="utf-8", errors="replace")
    session_id = f"cluster_test_{uuid.uuid4().hex[:8]}"

    try:
        out = upload_resume(base_url, session_id, text)
    except Exception as e:
        print("Upload failed:", e)
        return 1

    upload_id = out.get("upload_id")
    if not upload_id:
        print("Upload response missing upload_id:", out)
        return 1

    status, detail = poll_until_ready(base_url, upload_id)
    if status != "ready":
        print("Processing failed:", status, detail or "")
        return 1

    try:
        cr = cluster_experience(base_url, session_id)
    except Exception as e:
        print("Cluster request failed:", e)
        return 1

    clusters = cr.get("clusters") or []
    if not clusters:
        print("No clusters in response.")
        return 1

    dist = cluster_distribution_from_response(cr)
    has_standard = any(dist.get(c, 0) > 0 for c in CLUSTERS)

    print("Cluster assignment and percentage\n")
    if has_standard:
        for c in CLUSTERS:
            pct = dist.get(c, 0.0)
            count = next(
                (len(g.get("items") or []) for g in clusters if g.get("cluster_id") == c),
                0,
            )
            s = "item" if count == 1 else "items"
            print(f"  {c}: {pct * 100:5.1f}%  ({count} {s})")
    else:
        total_items = sum(len(g.get("items") or []) for g in clusters)
        for g in clusters:
            label = (g.get("cluster_label") or g.get("cluster_id") or "unknown").strip()
            items = g.get("items") or []
            n = len(items)
            pct = n / total_items if total_items else 0.0
            s = "item" if n == 1 else "items"
            print(f"  {label}: {pct * 100:5.1f}%  ({n} {s})")

    print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Resume-only clustering test: output cluster assignment and percentage.")
    ap.add_argument("--resume", "-r", default="test_fixtures/resume.txt", help="Path to resume (TXT)")
    ap.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = ap.parse_args()

    path = _resolve_resume_path(args.resume)
    return run(args.base_url, path)


if __name__ == "__main__":
    sys.exit(main())
