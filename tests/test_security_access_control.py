import os
import sys
import pytest
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

def test_unauthenticated_ack_pdf_access_blocked(client):
    """
    Test that an unauthenticated visitor cannot directly access acknowledgment PDFs.
    Should return 401, 403, or redirect to login (302).
    """
    response = client.get("/ack/1.pdf")
    assert response.status_code in (302, 401, 403), f"Expected auth challenge, got {response.status_code}"

def test_idor_prevented_on_view_application(client):
    """
    Test that a logged-in citizen cannot view another citizen's application details (IDOR).
    User logged in as mobile '9999999999' should get 403 Forbidden when accessing application belonging to '8888888888'.
    """
    mock_row = (
        "SSP25000001", "Citizen A", "8888888888", "1955-01-01",
        "Village X", "Block Y", "1234567890", "SBIN0001",
        "PENDING", "2026-01-01", None
    )
    
    with patch.object(main_app, "get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = mock_row

        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9999999999"  # Different mobile number
            sess["admin"] = False

        response = client.get("/application/1")
        # Must be blocked with 403 Forbidden because mobile does not match
        assert response.status_code == 403, f"Expected 403 Forbidden for IDOR, got {response.status_code}"
