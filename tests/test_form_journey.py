import os
import sys
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import app as main_app
app = main_app.app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-key"
    with app.test_client() as client:
        yield client

def test_indian_date_parsing_prioritizes_dmy(client):
    """
    Test that Indian date format DD/MM/YYYY is parsed correctly in declaration.
    '05/07/1955' must be interpreted as 5th July 1955 (month=7), NOT May 7th (month=5).
    """
    with patch.object(main_app, "get_db") as mock_get_db, \
         patch.object(main_app, "send_sms"):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_row = ("SSP26000001", "Test User", "9876543210", "1955-07-05", "Milanpur", "Borgaon", "1234567890", "SBIN0001", "2026-01-01", "PENDING")
        mock_cur.fetchone.side_effect = [(0,), (1,), (0,), mock_row]

        with client.session_transaction() as sess:
            sess["verified_mobile"] = "9876543210"
            sess["doc_path"] = "uploads/dummy.pdf"
            sess["form_data"] = {
                "applicant_name": "Test User",
                "gender": "Male",
                "marital_status": "Married",
                "village": "Milanpur",
                "block": "Borgaon",
                "bank_account": "1234567890",
                "ifsc": "SBIN0001",
                "dob": "05/07/1955"  # 5th July 1955 (in Indian DD/MM/YYYY)
            }

        client.post("/declaration", data={"agree": "1"})

        # Verify the inserted dob date object has month=7
        # Find the INSERT query call in call_args_list
        insert_call = [c for c in mock_cur.execute.call_args_list if "INSERT INTO applications" in c[0][0]][0]
        insert_args = insert_call[0][1]
        inserted_dob = insert_args[3]  # dob
        assert inserted_dob.month == 7, f"Expected month 7 (July), got {inserted_dob.month}"
        assert inserted_dob.day == 5, f"Expected day 5, got {inserted_dob.day}"

def test_widow_applicant_does_not_require_husband_employer(client):
    """
    Test that a widowed applicant without deceased husband employer
    is allowed to submit declaration without getting redirected back to step 1.
    """
    with patch.object(main_app, "get_db") as mock_get_db, \
         patch.object(main_app, "send_sms"):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_row = ("SSP26000001", "Runu Dutta", "9876543210", "1950-01-01", "Milanpur", "Borgaon", "1234567890", "SBIN0001", "2026-01-01", "PENDING")
        mock_cur.fetchone.side_effect = [(0,), (1,), (0,), mock_row]

        with client.session_transaction() as sess:
            sess["verified_mobile"] = "9876543210"
            sess["doc_path"] = "uploads/dummy.pdf"
            sess["form_data"] = {
                "applicant_name": "Runu Dutta",
                "gender": "Female",
                "marital_status": "Widowed",
                "husband_name": "",  # Optional for widows
                "husband_employer": "",  # Impossible for widows
                "village": "Milanpur",
                "block": "Borgaon",
                "bank_account": "1234567890",
                "ifsc": "SBIN0001",
                "dob": "01/01/1950"
            }

        response = client.post("/declaration", data={"agree": "1"}, follow_redirects=False)
        # Should succeed with 200 and render confirmation page, NOT redirect to form_step 1 (302)
        assert response.status_code == 200
        assert b"Application Submitted" in response.data

def test_upload_errors_are_user_friendly(client):
    """
    Test that invalid uploads display clear user-friendly error messages
    rather than cryptic technical codes like 'ERR_VAL_47'.
    """
    with client.session_transaction() as sess:
        sess["verified_mobile"] = "9876543210"
        sess["form_data"] = {"dob": "1950-01-01"}

    # Attempt upload with non-pdf file
    data = {"document": (b"dummy text content", "test.txt")}
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    page_text = response.get_data(as_text=True)
    assert "ERR_VAL_47" not in page_text, "Found cryptic 'ERR_VAL_47' in response"
