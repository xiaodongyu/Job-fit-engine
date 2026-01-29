"""Pytest for resume-only clustering: upload resume, cluster, output assignment and percentage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "tests" / "test_resume_only_clustering.py"
RESUME = PROJECT_ROOT / "test_fixtures" / "resume.txt"


@pytest.fixture
def resume_path() -> Path:
    return RESUME


def test_resume_only_clustering_outputs_assignment_and_percentage(resume_path: Path) -> None:
    """Run resume-only clustering script; assert it exits 0 and prints cluster assignment and percentage."""
    if not resume_path.exists():
        pytest.skip(f"Resume fixture not found: {resume_path}")
    if not SCRIPT.exists():
        pytest.skip(f"Script not found: {SCRIPT}")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--resume", str(resume_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, (
        f"Script failed (exit {result.returncode}). stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    )
    assert "Cluster assignment and percentage" in result.stdout
    assert "%" in result.stdout
