#!/usr/bin/env python3
"""
Single resume–JD match test: upload resume, match to one JD, print debug (contents sent to Gemini) and results.

Usage:
  python scripts/test_single_resume_jd_match.py [--resume PATH] [--jd PATH] [--base-url URL]

Defaults: Resume_1_MLE_Enriched.txt, JD_MLE_02_Amazon_GenAIIC.pdf.
Backend must be running. JD can be PDF (parsed via PyMuPDF) or TXT.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from qa_helpers import (
    health_check,
    match_by_cluster,
    parse_jd_pdf,
    poll_until_ready,
    resolve_jd_pdf,
    resolve_resume,
    upload_resume,
)


def _resolve_path(kind: str, val: str) -> Path:
    p = Path(val)
    if "/" in val or "\\" in val:
        if not p.is_absolute():
            p = _PROJECT_ROOT / p
        return p
    if kind == "resume":
        return resolve_resume(val)
    return resolve_jd_pdf(val)


def _load_jd_text(jd_path: Path) -> str:
    if jd_path.suffix.lower() == ".pdf":
        return parse_jd_pdf(jd_path)
    return jd_path.read_text(encoding="utf-8", errors="replace")


def run(base_url: str, resume_path: Path, jd_path: Path) -> int:
    base_url = base_url.rstrip("/")
    if not health_check(base_url):
        print("Backend not reachable at", base_url, "- start it first.")
        return 1

    if not resume_path.exists():
        print("Resume not found:", resume_path)
        return 1
    if not jd_path.exists():
        print("JD not found:", jd_path)
        return 1

    resume_text = resume_path.read_text(encoding="utf-8", errors="replace")
    jd_text = _load_jd_text(jd_path)
    session_id = f"single_match_{uuid.uuid4().hex[:8]}"

    try:
        out = upload_resume(base_url, session_id, resume_text)
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
        mc = match_by_cluster(base_url, session_id, jd_text, debug=True)
    except Exception as e:
        print("Match-by-cluster failed:", e)
        return 1

    debug = mc.get("debug")
    if debug:
        print("\n=== DEBUG: Contents sent to Gemini ===\n")
        print("--- System prompt ---")
        print(debug.get("system_prompt", "")[:800])
        if len(debug.get("system_prompt", "")) > 800:
            print("... [truncated]")
        print()
        print("--- Clusters (MLE/DS/SWE/QR/QD + items) ---")
        for c in debug.get("clusters", []):
            print(f"  {c.get('cluster_id')} ({c.get('cluster_label')}): {c.get('items_count')} items")
            for it in c.get("items", [])[:5]:
                print(f"    - [{it.get('label')}] {it.get('text', '')[:80]}...")
            if len(c.get("items", [])) > 5:
                print(f"    ... and {len(c['items']) - 5} more")
        print()
        print("--- Resume chunks ---")
        for ch in debug.get("resume_chunks", []):
            print(f"  [{ch.get('chunk_id')}] {ch.get('text', '')[:120]}...")
        print()
        print("--- JD chunks ---")
        for ch in debug.get("jd_chunks", []):
            print(f"  [{ch.get('chunk_id')}] {ch.get('text', '')[:120]}...")
        print()
        print("--- User prompt (full) ---")
        print(debug.get("user_prompt", ""))
        print()

    print("=== RESULTS ===\n")
    ov = mc.get("overall_match_pct")
    print("overall_match_pct:", ov if ov is not None else "null")
    print("\ncluster_matches:")
    for m in mc.get("cluster_matches", []):
        cluster = m.get("cluster", "")
        pct = m.get("match_pct")
        if pct is None:
            pct = 0.0
        ev = m.get("evidence", {})
        rn = len(ev.get("resume_chunks") or [])
        jn = len(ev.get("jd_chunks") or [])
        print(f"  {cluster}: {pct:.3f}  (resume chunks: {rn}, jd chunks: {jn})")
    print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Single resume–JD match test with debug output (contents sent to Gemini + results)."
    )
    ap.add_argument(
        "--resume", "-r",
        default="Resume_1_MLE_Enriched.txt",
        help="Resume file (default: Resume_1_MLE_Enriched.txt under quant benchmark)",
    )
    ap.add_argument(
        "--jd", "-j",
        default="JD_MLE_02_Amazon_GenAIIC.pdf",
        help="JD file PDF or TXT (default: JD_MLE_02_Amazon_GenAIIC.pdf)",
    )
    ap.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = ap.parse_args()

    resume_path = _resolve_path("resume", args.resume)
    jd_path = _resolve_path("jd", args.jd)
    return run(args.base_url, resume_path, jd_path)


if __name__ == "__main__":
    sys.exit(main())
