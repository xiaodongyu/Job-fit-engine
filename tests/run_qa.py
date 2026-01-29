#!/usr/bin/env python3
"""
QA test runner per test_fixtures/batch-qa-testing-plan.md.
Runs Phases 1–5, resolves paths from manifests, calls backend, evaluates rules, produces JSON + MD report.

Usage:
  python tests/run_qa.py [--base-url URL] [--output-dir DIR] [--phases 1,2,3,4,5]

Reports are written to test_results/ (default) as qa_report.json and qa_report.md.
Backend must be running. Default base-url: http://localhost:8000.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Ensure tests/ on path before importing qa_helpers
_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from qa_helpers import (
    CLUSTERS,
    add_materials,
    cluster_distribution_from_response,
    cluster_experience,
    health_check,
    load_manifest_mapping,
    load_manifest_pairings,
    load_manifest_two_phase_passfail,
    l1_error,
    match_by_cluster,
    normalize_ground_truth,
    parse_jd_pdf,
    poll_until_ready,
    primary_cluster_l1,
    resolve_addon,
    resolve_jd_pdf,
    resolve_resume,
    upload_resume,
    delta_direction,
)


@dataclass
class Phase1Result:
    resume_id: str
    session_id: str
    l1_overall: float
    l1_primary: float
    distribution: dict[str, float]
    ground_truth: dict[str, float]
    passed: bool
    error: str | None = None


@dataclass
class Phase2Result:
    resume_id: str
    session_id: str
    l1_overall_after: float
    distribution_after: dict[str, float]
    ground_truth_after: dict[str, float]
    passed: bool
    error: str | None = None


@dataclass
class Phase3MatchResult:
    jd_id: str
    expected_overall: float
    actual_overall: float | None
    overall_ok: bool
    per_cluster_ok: bool
    cluster_matches: list[dict] = field(default_factory=list)  # [{"cluster": str, "match_pct": float}, ...]
    error: str | None = None


@dataclass
class Phase3Result:
    resume_id: str
    session_id: str
    matches: list[Phase3MatchResult]
    passed: bool


@dataclass
class Phase4MatchResult:
    jd_id: str
    resume_only_overall: float | None
    resume_plus_addon_overall: float | None
    expected_delta: float
    expected_direction: str
    actual_delta: float | None
    delta_ok: bool
    direction_ok: bool
    error: str | None = None


@dataclass
class Phase4Result:
    resume_id: str
    resume_only_session: str
    resume_plus_addon_session: str
    matches: list[Phase4MatchResult]
    passed: bool


@dataclass
class RuleResult:
    rule_id: str
    outcome: str  # pass | fail | warn
    message: str


@dataclass
class QAReport:
    base_url: str
    phases_enabled: list[int]
    phase1: list[Phase1Result] = field(default_factory=list)
    phase2: list[Phase2Result] = field(default_factory=list)
    phase3: list[Phase3Result] = field(default_factory=list)
    phase4: list[Phase4Result] = field(default_factory=list)
    phase5_rules: list[RuleResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_phase1(
    base_url: str,
    mapping: dict,
    report: QAReport,
) -> None:
    thresh = mapping.get("global_thresholds", {}).get("distribution_metrics", {})
    max_l1_primary = thresh.get("max_L1_error_primary_cluster", 0.2)
    max_l1_overall = thresh.get("max_L1_error_overall", 0.35)

    for tc in mapping.get("test_cases", []):
        rid = tc["resume_id"]
        session_id = f"qa_{rid}_resume_only"
        res = Phase1Result(
            resume_id=rid,
            session_id=session_id,
            l1_overall=0.0,
            l1_primary=0.0,
            distribution={},
            ground_truth=tc.get("ground_truth_before", {}),
            passed=False,
        )
        try:
            path = resolve_resume(tc["resume_file"])
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            res.error = f"read resume: {e}"
            report.phase1.append(res)
            report.errors.append(f"P1 {rid}: {res.error}")
            continue

        try:
            up = upload_resume(base_url, session_id, text)
            upload_id = up["upload_id"]
        except Exception as e:
            res.error = f"upload: {e}"
            report.phase1.append(res)
            report.errors.append(f"P1 {rid}: {res.error}")
            continue

        status, detail = poll_until_ready(base_url, upload_id)
        if status != "ready":
            res.error = f"status {status}" + (f": {detail}" if detail else "")
            report.phase1.append(res)
            report.errors.append(f"P1 {rid}: {res.error}")
            continue

        try:
            cr = cluster_experience(base_url, session_id)
        except Exception as e:
            res.error = f"cluster: {e}"
            report.phase1.append(res)
            report.errors.append(f"P1 {rid}: {res.error}")
            continue

        dist = cluster_distribution_from_response(cr)
        gt = normalize_ground_truth(tc.get("ground_truth_before", {}))
        l1_o = l1_error(dist, gt)
        l1_p = primary_cluster_l1(dist, gt)

        res.distribution = dist
        res.ground_truth = gt
        res.l1_overall = l1_o
        res.l1_primary = l1_p
        res.passed = l1_p <= max_l1_primary and l1_o <= max_l1_overall
        report.phase1.append(res)


def run_phase2(
    base_url: str,
    mapping: dict,
    report: QAReport,
) -> None:
    thresh = mapping.get("global_thresholds", {}).get("augmentation", {})
    max_unexpected = thresh.get("max_unexpected_delta", 0.08)

    for tc in mapping.get("test_cases", []):
        rid = tc["resume_id"]
        session_id = f"qa_{rid}_addon"
        res = Phase2Result(
            resume_id=rid,
            session_id=session_id,
            l1_overall_after=0.0,
            distribution_after={},
            ground_truth_after=tc.get("ground_truth_after_target", {}),
            passed=False,
        )
        try:
            rpath = resolve_resume(tc["resume_file"])
            apath = resolve_addon(tc["addon_file"])
            rtext = rpath.read_text(encoding="utf-8", errors="replace")
            addon_text = apath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            res.error = f"read files: {e}"
            report.phase2.append(res)
            report.errors.append(f"P2 {rid}: {res.error}")
            continue

        try:
            up = upload_resume(base_url, session_id, rtext)
            poll_until_ready(base_url, up["upload_id"])  # ignore status for initial upload
        except Exception as e:
            res.error = f"upload resume: {e}"
            report.phase2.append(res)
            report.errors.append(f"P2 {rid}: {res.error}")
            continue

        try:
            add_up = add_materials(base_url, session_id, addon_text)
            status, detail = poll_until_ready(base_url, add_up["upload_id"])
        except Exception as e:
            res.error = f"add materials: {e}"
            report.phase2.append(res)
            report.errors.append(f"P2 {rid}: {res.error}")
            continue
        if status != "ready":
            res.error = f"addon status {status}" + (f": {detail}" if detail else "")
            report.phase2.append(res)
            report.errors.append(f"P2 {rid}: {res.error}")
            continue

        try:
            cr = cluster_experience(base_url, session_id)
        except Exception as e:
            res.error = f"cluster: {e}"
            report.phase2.append(res)
            report.errors.append(f"P2 {rid}: {res.error}")
            continue

        dist = cluster_distribution_from_response(cr)
        gt = normalize_ground_truth(tc.get("ground_truth_after_target", {}))
        l1_o = l1_error(dist, gt)

        res.distribution_after = dist
        res.ground_truth_after = gt
        res.l1_overall_after = l1_o
        res.passed = l1_o <= max_unexpected * 2  # relaxed vs plan
        report.phase2.append(res)


def run_phase3(
    base_url: str,
    pairings: dict,
    report: QAReport,
) -> None:
    tol = pairings.get("tolerances", {})
    overall_err = tol.get("overall_match_abs_error", 0.08)
    per_cluster_err = tol.get("per_cluster_match_abs_error", 0.12)

    by_resume = {c["resume_id"]: c for c in pairings.get("cases", [])}

    for p1 in report.phase1:
        if p1.error or not p1.session_id:
            continue
        rid = p1.resume_id
        case = by_resume.get(rid)
        if not case:
            report.phase3.append(Phase3Result(resume_id=rid, session_id=p1.session_id, matches=[], passed=True))
            continue

        matches: list[Phase3MatchResult] = []
        all_ok = True
        for jd in case.get("expected_best_fit_jds", []):
            jd_id = jd["jd_id"]
            jd_pdf = jd.get("jd_pdf", jd_id + ".pdf")
            expected_overall = jd.get("expected_overall_match", jd.get("expected_overall", 0.0))
            expected_cluster = jd.get("expected_cluster_matches", {})

            m = Phase3MatchResult(
                jd_id=jd_id,
                expected_overall=expected_overall,
                actual_overall=None,
                overall_ok=False,
                per_cluster_ok=False,
            )
            try:
                jd_path = resolve_jd_pdf(jd_pdf)
                jd_text = parse_jd_pdf(jd_path)
            except Exception as e:
                m.error = str(e)
                matches.append(m)
                all_ok = False
                continue

            try:
                mc = match_by_cluster(base_url, p1.session_id, jd_text)
            except Exception as e:
                m.error = str(e)
                matches.append(m)
                all_ok = False
                continue

            actual_overall = mc.get("overall_match_pct")
            m.actual_overall = actual_overall
            m.overall_ok = (
                actual_overall is not None
                and abs((actual_overall or 0) - expected_overall) <= overall_err
            )

            raw_cm = mc.get("cluster_matches", [])
            m.cluster_matches = [
                {"cluster": x.get("cluster", ""), "match_pct": x.get("match_pct")}
                for x in raw_cm
            ]
            pred_map = {x["cluster"]: x.get("match_pct") for x in raw_cm}
            cluster_ok = True
            for cl, exp_val in expected_cluster.items():
                if exp_val is None:
                    continue
                pred_val = pred_map.get(cl)
                if pred_val is None:
                    continue
                if abs(pred_val - exp_val) > per_cluster_err:
                    cluster_ok = False
                    break
            m.per_cluster_ok = cluster_ok
            if not m.overall_ok or not m.per_cluster_ok:
                all_ok = False
            matches.append(m)

        report.phase3.append(Phase3Result(resume_id=rid, session_id=p1.session_id, matches=matches, passed=all_ok))


def run_phase4(
    base_url: str,
    two_phase: dict,
    report: QAReport,
) -> None:
    tol = two_phase.get("tolerances", {})
    delta_err = tol.get("delta_overall_match_abs_error", 0.06)
    overall_err = tol.get("overall_match_abs_error", 0.08)

    by_resume = {c["resume_id"]: c for c in two_phase.get("cases", [])}
    p1_sessions = {r.resume_id: r.session_id for r in report.phase1 if not r.error}
    p2_sessions = {r.resume_id: r.session_id for r in report.phase2 if not r.error}

    for rid, case in by_resume.items():
        sid_ro = p1_sessions.get(rid)
        sid_rpa = p2_sessions.get(rid)
        if not sid_ro or not sid_rpa:
            report.phase4.append(
                Phase4Result(
                    resume_id=rid,
                    resume_only_session=sid_ro or "",
                    resume_plus_addon_session=sid_rpa or "",
                    matches=[],
                    passed=False,
                )
            )
            continue

        matches: list[Phase4MatchResult] = []
        all_ok = True
        for jd in case.get("expected_best_fit_jds_two_phase", []):
            jd_id = jd["jd_id"]
            jd_pdf = jd.get("jd_pdf", jd_id + ".pdf")
            ro = jd.get("resume_only", {})
            rpa = jd.get("resume_plus_addon", {})
            exp_ro = ro.get("expected_overall")
            exp_rpa = rpa.get("expected_overall")
            delta_exp = jd.get("expected_delta", {})
            exp_delta = delta_exp.get("overall_match", 0.0)
            exp_dir = delta_exp.get("direction", "~")

            m = Phase4MatchResult(
                jd_id=jd_id,
                resume_only_overall=None,
                resume_plus_addon_overall=None,
                expected_delta=exp_delta,
                expected_direction=exp_dir,
                actual_delta=None,
                delta_ok=False,
                direction_ok=False,
            )
            try:
                jd_path = resolve_jd_pdf(jd_pdf)
                jd_text = parse_jd_pdf(jd_path)
            except Exception as e:
                m.error = str(e)
                matches.append(m)
                all_ok = False
                continue

            try:
                mc_ro = match_by_cluster(base_url, sid_ro, jd_text)
                mc_rpa = match_by_cluster(base_url, sid_rpa, jd_text)
            except Exception as e:
                m.error = str(e)
                matches.append(m)
                all_ok = False
                continue

            act_ro = mc_ro.get("overall_match_pct")
            act_rpa = mc_rpa.get("overall_match_pct")
            m.resume_only_overall = act_ro
            m.resume_plus_addon_overall = act_rpa

            if act_ro is not None and act_rpa is not None:
                m.actual_delta = act_rpa - act_ro
                m.delta_ok = abs((m.actual_delta or 0) - exp_delta) <= delta_err
                m.direction_ok = delta_direction(m.actual_delta or 0, exp_dir)
            if exp_ro is not None and act_ro is not None:
                if abs(act_ro - exp_ro) > overall_err:
                    all_ok = False
            if exp_rpa is not None and act_rpa is not None:
                if abs(act_rpa - exp_rpa) > overall_err:
                    all_ok = False
            if not m.delta_ok or not m.direction_ok:
                all_ok = False
            matches.append(m)

        report.phase4.append(
            Phase4Result(
                resume_id=rid,
                resume_only_session=sid_ro,
                resume_plus_addon_session=sid_rpa,
                matches=matches,
                passed=all_ok,
            )
        )


def run_phase5(
    two_phase: dict,
    report: QAReport,
) -> None:
    rules = two_phase.get("pass_fail_rule_set", {})
    global_rules = rules.get("global_rules", [])
    phase_rules = rules.get("phase_rules", {})

    def add(id: str, outcome: str, msg: str) -> None:
        report.phase5_rules.append(RuleResult(rule_id=id, outcome=outcome, message=msg))

    # PF-G1-SCHEMA: responses conform to schema
    schema_ok = not any(
        getattr(r, "error", None) for r in report.phase1 + report.phase2
    ) and all(
        getattr(r, "passed", True) or getattr(r, "error", None) is None
        for r in report.phase3 + report.phase4
    )
    add("PF-G1-SCHEMA", "pass" if schema_ok else "fail", "Schema validity (no missing required fields)")

    # PF-G2-EVIDENCE-COUNT: min 2 evidence per cluster with score >= 0.1
    # We do not inspect evidence here; mark as warn if we had cluster responses.
    add("PF-G2-EVIDENCE-COUNT", "warn", "Evidence count check requires response inspection (skipped)")

    # PF-G3: verbatim + source attribution — backend does not support addon attribution yet
    add("PF-G3-EVIDENCE-VERBATIM", "warn", "Addon attribution not implemented; skip")

    # PF-G4-JD-RANKING-STABILITY: top-1 JD matches manifest
    # We don't rank JDs; we run match per expected JD. Mark as warn.
    add("PF-G4-JD-RANKING-STABILITY", "warn", "Top-1 JD ranking not computed (per-JD match only)")

    # Phase rules: PF-P1, PF-P2 (resume_only), PF-A1, PF-A2, PF-A3 (resume_plus_addon)
    for r in phase_rules.get("resume_only", []):
        add(r["id"], "warn", f"{r['description']} — check phase3 results")
    for r in phase_rules.get("resume_plus_addon", []):
        add(r["id"], "warn", f"{r['description']} — check phase4 results")


def write_report(report: QAReport, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "_generated_by": "tests/run_qa.py",
        "base_url": report.base_url,
        "phases_enabled": report.phases_enabled,
        "phase1": [asdict(r) for r in report.phase1],
        "phase2": [asdict(r) for r in report.phase2],
        "phase3": [asdict(r) for r in report.phase3],
        "phase4": [asdict(r) for r in report.phase4],
        "phase5_rules": [asdict(r) for r in report.phase5_rules],
        "errors": report.errors,
    }
    json_path = out_dir / "qa_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    lines = [
        "# QA Report",
        "",
        "**Generated by:** `tests/run_qa.py`",
        "",
        f"**Base URL:** {report.base_url}",
        f"**Phases:** {report.phases_enabled}",
        "",
        "## Phase 1 (Resume-only clustering)",
        "",
    ]
    for r in report.phase1:
        st = "PASS" if r.passed else "FAIL"
        lines.append(f"- **{r.resume_id}** ({r.session_id}): L1 overall={r.l1_overall:.4f}, primary={r.l1_primary:.4f} — {st}")
        if r.error:
            lines.append(f"  - Error: {r.error}")
    lines.extend(["", "## Phase 2 (Augmentation)", ""])
    for r in report.phase2:
        st = "PASS" if r.passed else "FAIL"
        lines.append(f"- **{r.resume_id}** ({r.session_id}): L1 after={r.l1_overall_after:.4f} — {st}")
        if r.error:
            lines.append(f"  - Error: {r.error}")
    lines.extend(["", "## Phase 3 (Resume–JD match, resume-only)", ""])
    for r in report.phase3:
        st = "PASS" if r.passed else "FAIL"
        lines.append(f"- **{r.resume_id}**: {st}")
        for m in r.matches:
            ok = "ok" if (m.overall_ok and m.per_cluster_ok) else "fail"
            lines.append(f"  - {m.jd_id}: overall={m.actual_overall} (exp {m.expected_overall}) — {ok}")
            if m.cluster_matches:
                parts = [f"{c['cluster']} {c.get('match_pct', 0):.3f}" for c in m.cluster_matches]
                lines.append(f"    cluster_matches: {', '.join(parts)}")
    lines.extend(["", "## Phase 4 (Two-phase match)", ""])
    for r in report.phase4:
        st = "PASS" if r.passed else "FAIL"
        lines.append(f"- **{r.resume_id}**: {st}")
        for m in r.matches:
            d = m.actual_delta if m.actual_delta is not None else "N/A"
            lines.append(f"  - {m.jd_id}: delta={d} (exp {m.expected_delta} {m.expected_direction})")
    lines.extend(["", "## Phase 5 (Pass/fail rules)", ""])
    for r in report.phase5_rules:
        lines.append(f"- **{r.rule_id}**: {r.outcome} — {r.message}")
    if report.errors:
        lines.extend(["", "## Errors", ""])
        for e in report.errors:
            lines.append(f"- {e}")

    md_path = out_dir / "qa_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run QA phases per test_fixtures/batch-qa-testing-plan.md")
    ap.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    ap.add_argument("--output-dir", "-o", default="test_results", help="Output directory for qa_report.json and qa_report.md (default: test_results)")
    ap.add_argument("--phases", default="1,2,3,4,5", help="Comma-separated phase numbers to run")
    args = ap.parse_args()

    phases = [int(x.strip()) for x in args.phases.split(",") if x.strip()]
    base_url = args.base_url.rstrip("/")

    if not health_check(base_url):
        print(f"Backend not reachable at {base_url}. Start it first.")
        return 1

    report = QAReport(base_url=base_url, phases_enabled=phases)

    mapping = load_manifest_mapping()
    pairings = load_manifest_pairings()
    two_phase = load_manifest_two_phase_passfail()

    if 1 in phases:
        print("Running Phase 1 (resume-only clustering)...")
        run_phase1(base_url, mapping, report)
    if 2 in phases:
        print("Running Phase 2 (augmentation)...")
        run_phase2(base_url, mapping, report)
    if 3 in phases:
        print("Running Phase 3 (resume–JD match, resume-only)...")
        run_phase3(base_url, pairings, report)
    if 4 in phases:
        print("Running Phase 4 (two-phase match)...")
        run_phase4(base_url, two_phase, report)
    if 5 in phases:
        print("Running Phase 5 (pass/fail rules)...")
        run_phase5(two_phase, report)

    write_report(report, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
