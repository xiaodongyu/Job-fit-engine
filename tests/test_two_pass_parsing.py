#!/usr/bin/env python3
"""
Tests for two-pass resume parsing pipeline.

Unit tests for preprocessing (no LLM needed).
Integration tests for full pipeline (requires backend or mocked LLM).

Usage:
  # Unit tests only (no backend needed):
  pytest tests/test_two_pass_parsing.py -k "unit"
  
  # Integration tests (backend must be running):
  pytest tests/test_two_pass_parsing.py -k "integration" --base-url http://localhost:8000
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend to path for imports
_TESTS = Path(__file__).resolve().parent
_PROJECT_ROOT = _TESTS.parent
_BACKEND = _PROJECT_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


# === Test Data ===

# Sample resume text with tabs (like from .docx extraction)
# Uses fictional placeholder data - do NOT use real personal information
SAMPLE_RESUME_WITH_TABS = """\
JANE DOE
Anytown, USA | +1 (555) 123-4567 | jane.doe@example.com
EDUCATION
Example University\t  New York, USA
Master of Science, Computer Science\t\tSept. 2023 – Dec. 2024
GPA: 3.90; Dean's List
Relevant Coursework: Machine Learning, Data Structures, Algorithms, Computer Vision.
State College\tBoston, USA 
Bachelor of Science, Mathematics\tSept. 2019 – May 2023
GPA: 3.75; Cum laude
Relevant Coursework: Statistics, Linear Algebra, Calculus, Programming.
SKILLS
Skills: Data Analysis, Statistical Modeling, Software Development
Tools & Platforms: Git, AWS, Docker
Programming Languages: Python, Java, SQL
Languages: English (Native)
WORK EXPERIENCE
TechCorp Inc.\tAnytown, USA
Software Engineer\tFeb. 2025 – Present
Developed machine learning models for data classification tasks.
Built and optimized backend services using Python and Java.
Collaborated with cross-functional teams on product development.
DataStartup LLC\tRemote
Data Analyst Intern\tJun. 2024 – Aug. 2024
Designed automated data pipelines for ETL processes.
Applied statistical methods to analyze business metrics.
Created dashboards and reports for stakeholder presentations.
RELEVANT PROJECTS
Portfolio Optimizer\t 
Self-Project\t\tJan. 2026
Built a portfolio optimization tool using modern portfolio theory.
Implemented backtesting framework to evaluate strategy performance.
"""


# === Unit Tests (no LLM needed) ===

class TestPreprocessing:
    """Unit tests for _preprocess_resume_text function."""
    
    def test_tabs_converted_to_pipes(self):
        """Verify tabs are converted to ' | ' separators."""
        from rag import _preprocess_resume_text
        
        result = _preprocess_resume_text(SAMPLE_RESUME_WITH_TABS)
        
        # Should not contain any tabs
        assert "\t" not in result, "Tabs should be converted to pipes"
        
        # Should contain pipes where tabs were
        assert "Example University | New York, USA" in result
        assert "TechCorp Inc. | Anytown, USA" in result
        assert "Software Engineer | Feb. 2025 – Present" in result
    
    def test_multiple_tabs_collapsed(self):
        """Verify multiple consecutive tabs become single pipe."""
        from rag import _preprocess_resume_text
        
        text_with_multiple_tabs = "Company\t\t\tLocation"
        result = _preprocess_resume_text(text_with_multiple_tabs)
        
        assert result == "Company | Location"
    
    def test_excessive_whitespace_cleaned(self):
        """Verify multiple spaces are collapsed to single space."""
        from rag import _preprocess_resume_text
        
        text_with_spaces = "Hello    World     Test"
        result = _preprocess_resume_text(text_with_spaces)
        
        assert result == "Hello World Test"
    
    def test_lines_stripped(self):
        """Verify leading/trailing whitespace is removed from lines."""
        from rag import _preprocess_resume_text
        
        text_with_whitespace = "  Line 1  \n   Line 2   "
        result = _preprocess_resume_text(text_with_whitespace)
        
        lines = result.split("\n")
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"


class TestPromptBuilding:
    """Unit tests for prompt building functions."""
    
    def test_segment_prompt_includes_text(self):
        """Verify segment prompt includes the resume text."""
        from prompts import build_resume_segment_prompt
        
        text = "Test resume content"
        prompt = build_resume_segment_prompt(text)
        
        assert "Test resume content" in prompt
        assert "=== RESUME TEXT ===" in prompt
        assert "blocks" in prompt.lower()
    
    def test_map_prompt_includes_blocks(self):
        """Verify map prompt includes the blocks JSON."""
        from prompts import build_resume_map_prompt
        
        blocks_data = {
            "blocks": [
                {
                    "section": "experience",
                    "header_lines": ["Test Company | Location"],
                    "meta_lines": ["Title | Dates"],
                    "bullet_lines": ["Did something"],
                    "raw_lines": ["Test Company | Location", "Title | Dates", "Did something"]
                }
            ]
        }
        prompt = build_resume_map_prompt(blocks_data)
        
        assert "Test Company" in prompt
        assert "experiences" in prompt.lower()


class TestSchemaValidation:
    """Unit tests for schema definitions."""
    
    def test_segment_schema_has_blocks(self):
        """Verify segment schema defines blocks array."""
        from prompts import RESUME_SEGMENT_SCHEMA
        
        assert "blocks" in RESUME_SEGMENT_SCHEMA["properties"]
        blocks_schema = RESUME_SEGMENT_SCHEMA["properties"]["blocks"]
        assert blocks_schema["type"] == "array"
    
    def test_segment_block_has_required_fields(self):
        """Verify segment block schema has all required fields."""
        from prompts import RESUME_SEGMENT_SCHEMA
        
        block_schema = RESUME_SEGMENT_SCHEMA["properties"]["blocks"]["items"]
        required = block_schema.get("required", [])
        
        assert "section" in required
        assert "header_lines" in required
        assert "meta_lines" in required
        assert "bullet_lines" in required
        assert "raw_lines" in required


# === Integration Tests (requires backend or mocked LLM) ===

def pytest_addoption(parser):
    """Add command line options for integration tests."""
    parser.addoption("--base-url", default="http://localhost:8000", help="Backend URL")


class TestTwoPassIntegration:
    """Integration tests for two-pass parsing (requires running backend)."""
    
    def test_full_pipeline_extracts_company_and_location(self, request):
        """Test that two-pass parsing correctly extracts company and location."""
        import requests
        import uuid
        import time
        
        base_url = request.config.getoption("--base-url").rstrip("/")
        
        # Check backend is running
        try:
            r = requests.get(f"{base_url}/health", timeout=5)
            if r.status_code != 200:
                pytest.skip("Backend not available")
        except Exception:
            pytest.skip("Backend not available")
        
        # Upload resume with tabs
        session_id = f"test_twopass_{uuid.uuid4().hex[:8]}"
        r = requests.post(
            f"{base_url}/resume/upload/json",
            json={"text": SAMPLE_RESUME_WITH_TABS, "session_id": session_id}
        )
        assert r.status_code == 200, f"Upload failed: {r.text}"
        upload_id = r.json().get("upload_id")
        
        # Poll until ready
        for _ in range(30):
            r = requests.get(f"{base_url}/resume/status", params={"upload_id": upload_id})
            status = r.json().get("status")
            if status == "ready":
                break
            if status == "error":
                pytest.fail(f"Processing failed: {r.json()}")
            time.sleep(1)
        else:
            pytest.fail("Timeout waiting for processing")
        
        # Get structured resume
        r = requests.get(f"{base_url}/resume/structured", params={"session_id": session_id})
        assert r.status_code == 200, f"Failed to get structured: {r.text}"
        data = r.json()
        structured = data.get("structured", {})
        
        # Verify experiences have company and location
        experiences = structured.get("experiences", [])
        assert len(experiences) >= 1, "Should have at least one experience"
        
        # Check first experience (ZBeats Inc.)
        first_exp = experiences[0]
        assert first_exp.get("company") is not None, "Company should not be null"
        assert first_exp.get("location") is not None, "Location should not be null"
        
        # Check for specific values (case-insensitive check)
        company_lower = (first_exp.get("company") or "").lower()
        assert "techcorp" in company_lower or "datastartup" in company_lower, \
            f"Expected TechCorp or DataStartup, got {first_exp.get('company')}"
    
    def test_education_not_fragmented(self, request):
        """Test that education entries are consolidated, not fragmented."""
        import requests
        import uuid
        import time
        
        base_url = request.config.getoption("--base-url").rstrip("/")
        
        # Check backend is running
        try:
            r = requests.get(f"{base_url}/health", timeout=5)
            if r.status_code != 200:
                pytest.skip("Backend not available")
        except Exception:
            pytest.skip("Backend not available")
        
        # Upload resume with tabs
        session_id = f"test_edu_{uuid.uuid4().hex[:8]}"
        r = requests.post(
            f"{base_url}/resume/upload/json",
            json={"text": SAMPLE_RESUME_WITH_TABS, "session_id": session_id}
        )
        assert r.status_code == 200
        upload_id = r.json().get("upload_id")
        
        # Poll until ready
        for _ in range(30):
            r = requests.get(f"{base_url}/resume/status", params={"upload_id": upload_id})
            status = r.json().get("status")
            if status == "ready":
                break
            if status == "error":
                pytest.fail(f"Processing failed: {r.json()}")
            time.sleep(1)
        else:
            pytest.fail("Timeout waiting for processing")
        
        # Get structured resume
        r = requests.get(f"{base_url}/resume/structured", params={"session_id": session_id})
        data = r.json()
        structured = data.get("structured", {})
        
        # Verify education is not fragmented
        education = structured.get("education", [])
        
        # Should have exactly 2 education entries (Example University + State College)
        # Not 6+ fragmented entries
        assert len(education) <= 4, \
            f"Education should not be fragmented into many items, got {len(education)} entries"
        
        # Check that at least one entry has a school name
        schools = [e.get("school") for e in education if e.get("school")]
        assert len(schools) >= 1, "At least one education entry should have school name"
    
    def test_blocks_file_created(self, request):
        """Test that resume_blocks.json is created for debugging."""
        import requests
        import uuid
        import time
        
        base_url = request.config.getoption("--base-url").rstrip("/")
        
        # Check backend is running
        try:
            r = requests.get(f"{base_url}/health", timeout=5)
            if r.status_code != 200:
                pytest.skip("Backend not available")
        except Exception:
            pytest.skip("Backend not available")
        
        # Upload resume
        session_id = f"test_blocks_{uuid.uuid4().hex[:8]}"
        r = requests.post(
            f"{base_url}/resume/upload/json",
            json={"text": SAMPLE_RESUME_WITH_TABS, "session_id": session_id}
        )
        assert r.status_code == 200
        upload_id = r.json().get("upload_id")
        
        # Poll until ready
        for _ in range(30):
            r = requests.get(f"{base_url}/resume/status", params={"upload_id": upload_id})
            status = r.json().get("status")
            if status == "ready":
                break
            if status == "error":
                pytest.fail(f"Processing failed: {r.json()}")
            time.sleep(1)
        else:
            pytest.fail("Timeout waiting for processing")
        
        # Check that blocks file exists
        blocks_path = _PROJECT_ROOT / "backend" / "data" / "sessions" / session_id / "resume_blocks.json"
        assert blocks_path.exists(), f"Blocks file should be created at {blocks_path}"
        
        # Verify blocks file has content
        import json
        with open(blocks_path) as f:
            blocks_data = json.load(f)
        
        assert "blocks" in blocks_data
        assert len(blocks_data["blocks"]) > 0, "Blocks file should have at least one block"


# === CLI Runner ===

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"] + sys.argv[1:])
