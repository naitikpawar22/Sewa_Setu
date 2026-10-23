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

def test_citizen_cannot_approve_applications(client):
    """
    Test that a citizen logged in through the status portal (session['logged_in'] = True, session['admin'] = False)
    cannot approve applications via /admin/approve/<id> (Privilege Escalation).
    Must return 403 Forbidden.
    """
    with patch.object(main_app, "get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9876543210"
            sess["admin"] = False  # Not an admin!

        response = client.post("/admin/approve/1")
        assert response.status_code == 403, f"Expected 403 Forbidden for non-admin approve, got {response.status_code}"

def test_citizen_cannot_reject_applications(client):
    """
    Test that a citizen cannot reject applications via /admin/reject/<id>.
    Must return 403 Forbidden.
    """
    with patch.object(main_app, "get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9876543210"
            sess["admin"] = False

        response = client.post("/admin/reject/1")
        assert response.status_code == 403, f"Expected 403 Forbidden for non-admin reject, got {response.status_code}"

def test_citizen_cannot_view_admin_application_list(client):
    """
    Test that a citizen session cannot view the admin application queue.
    """
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["portal_mobile"] = "9876543210"
        sess["admin"] = False

    response = client.get("/admin/applications")
    assert response.status_code in (403, 302), f"Expected 403 or redirect, got {response.status_code}"
    if response.status_code == 302:
        assert response.headers["Location"].endswith("/admin/login") or response.headers["Location"].endswith("/admin")
