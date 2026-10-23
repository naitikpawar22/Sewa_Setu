import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import app as main_app

def test_indic_name_not_truncated_in_sanitize():
    """
    Test that Indic/Assamese names are not truncated by raw byte slicing to ~6 characters.
    A 12-character Assamese name must be preserved in full.
    """
    assamese_name = "প্ৰণিতা বৰুৱা"  # 12 characters, ~36 bytes in UTF-8
    cleaned = main_app.sanitize(assamese_name)
    assert cleaned == assamese_name, f"Expected full name '{assamese_name}', got '{cleaned}'"

def test_pdf_generation_preserves_indic_script():
    """
    Test that PDF acknowledgment slip preserves Indic/Assamese characters
    without throwing encoding exceptions or falling back to '?' question marks.
    """
    mock_cur = MagicMock()
    # Row matching SELECT in generate_acknowledgment:
    # application_no, applicant_name, mobile, dob, village, block, bank_account, ifsc, submitted_at, status
    mock_cur.fetchone.return_value = (
        "SSP26000001",
        "প্ৰণিতা বৰুৱা",
        "9876543210",
        "1950-01-01",
        "Milanpur",
        "Borgaon",
        "123456789012",
        "SBIN0001234",
        "2026-01-01 10:00:00",
        "PENDING"
    )
    
    pdf_bytes = main_app.generate_acknowledgment(mock_cur, 1)
    assert len(pdf_bytes) > 0, "PDF bytes should not be empty"
    import io, pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    extracted = "".join(p.extract_text() for p in reader.pages)
    assert "প্ৰণিতা" in extracted, f"Expected Assamese name in PDF, got: {extracted}"
