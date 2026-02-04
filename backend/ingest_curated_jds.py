#!/usr/bin/env python3
"""
Script to ingest curated JDs from test_fixtures into the global JD index.
Run this once to populate the curated JD index.

Usage:
    python ingest_curated_jds.py
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import fitz  # PyMuPDF
import rag


JD_FIXTURES_DIR = Path(__file__).parent.parent / "test_fixtures" / "jd_senior_us_mixed_roles"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        doc = fitz.open(str(pdf_path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""


def main():
    # Load jd_index.json
    index_path = JD_FIXTURES_DIR / "jd_index.json"
    if not index_path.exists():
        print(f"ERROR: {index_path} not found")
        return 1
    
    with open(index_path, "r", encoding="utf-8") as f:
        jd_index = json.load(f)
    
    items_to_ingest = []
    
    for item in jd_index.get("items", []):
        pdf_file = item.get("pdf_file")
        if not pdf_file:
            continue
        
        pdf_path = JD_FIXTURES_DIR / pdf_file
        if not pdf_path.exists():
            print(f"WARNING: PDF not found: {pdf_path}")
            continue
        
        # Extract text from PDF
        text = extract_pdf_text(pdf_path)
        if not text:
            print(f"WARNING: No text extracted from {pdf_file}")
            continue
        
        # Build JD item
        jd_item = {
            "title": item.get("jd_id", pdf_file),
            "role": item.get("role", "MLE"),
            "level": item.get("seniority", "Senior").lower(),  # Convert to lowercase
            "text": text
        }
        
        items_to_ingest.append(jd_item)
        print(f"Prepared: {jd_item['title']} ({jd_item['role']}, {jd_item['level']})")
    
    if not items_to_ingest:
        print("No JDs to ingest")
        return 1
    
    # Ingest into RAG
    print(f"\nIngesting {len(items_to_ingest)} JDs...")
    try:
        count = rag.ingest_jds(items_to_ingest)
        print(f"SUCCESS: Ingested {count} chunks from {len(items_to_ingest)} JDs")
        return 0
    except Exception as e:
        print(f"ERROR during ingestion: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
