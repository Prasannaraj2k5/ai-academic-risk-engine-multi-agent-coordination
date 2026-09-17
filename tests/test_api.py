"""Integration tests for all FastAPI endpoints using TestClient."""

import pytest
from starlette.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /health returns operational status and DB mode."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "active_database" in data
    assert isinstance(data["live_groq_llm"], bool)


def test_ask_endpoint():
    """Verify POST /ask answers natural language academic questions."""
    res = client.post("/ask", json={"question": "What is academic risk?"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["response"]) > 20
    assert "academic risk" in data["question"].lower()


def test_student_analyze_stu104():
    """Verify POST /students/analyze returns exact demonstration metrics for STU104."""
    res = client.post("/students/analyze", json={"student_id": "STU104"})
    assert res.status_code == 200
    data = res.json()
    
    assert data["student_id"] == "STU104"
    assert data["risk_score"] == 89
    assert data["risk_band"] == "CRITICAL"
    assert data["attendance_pct"] == 68.0
    assert data["current_average_pct"] == 54.7
    assert data["prior_average_pct"] == 74.0
    assert data["performance_delta"] == -19.3
    assert data["failed_assessments_count"] == 2
    assert data["missed_assignments_count"] == 2
    assert data["urgency"] == "Immediate"
    assert data["faculty_oversight"] == "Required"
    assert data["follow_up_period"] == "Within 7 Days"
    assert len(data["top_interventions"]) == 3


def test_student_analyze_invalid_id():
    """Verify POST /students/analyze returns 404 for unknown student and does not crash."""
    res = client.post("/students/analyze", json={"student_id": "STU999_NONEXISTENT"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_class_analyze_cohort():
    """Verify POST /class/analyze returns exact cohort distribution across 60 students."""
    res = client.post("/class/analyze", json={"section": "CSE-A"})
    assert res.status_code == 200
    data = res.json()
    
    assert data["total_students"] == 60
    dist = data["distribution"]
    assert dist["Critical"] == 2
    assert dist["High"] == 3
    assert dist["Medium"] == 10
    assert dist["Low"] == 45


def test_workflow_run_and_status():
    """Verify POST /workflow/run and GET /workflow/{id}/status."""
    res = client.post("/workflow/run", json={"query": "Analyze STU104", "student_id": "STU104"})
    assert res.status_code == 200
    wf_data = res.json()
    wf_id = wf_data["workflow_id"]
    assert wf_data["status"] == "COMPLETED"

    # Status check
    status_res = client.get(f"/workflow/{wf_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["workflow_id"] == wf_id
    assert status_res.json()["status"] == "COMPLETED"


def test_get_student_and_history():
    """Verify GET /students/{id} and GET /students/{id}/history."""
    res = client.get("/students/STU104")
    assert res.status_code == 200
    assert res.json()["name"] == "Rohan Verma"

    hist_res = client.get("/students/STU104/history")
    assert hist_res.status_code == 200
    assert "history" in hist_res.json()


def test_faculty_review_action():
    """Verify POST /review/action records Approve, Modify, and Reject decisions."""
    # Approve
    app_res = client.post("/review/action", json={
        "workflow_id": "wf-api-test-01",
        "student_id": "STU104",
        "faculty_action": "APPROVE",
        "feedback": "Approved attendance agreement",
        "reviewer_name": "Dr. K. Raman"
    })
    assert app_res.status_code == 200
    assert app_res.json()["action"] == "APPROVE"

    # Invalid action
    bad_res = client.post("/review/action", json={
        "workflow_id": "wf-api-test-02",
        "student_id": "STU104",
        "faculty_action": "INVALID_ACTION",
    })
    assert bad_res.status_code == 400


def test_metrics_and_agents_endpoints():
    """Verify GET /metrics and GET /agents return valid schema payloads."""
    m_res = client.get("/metrics")
    assert m_res.status_code == 200
    assert "workflow_count" in m_res.json()
    assert "tool_usage_counts" in m_res.json()

    a_res = client.get("/agents")
    assert a_res.status_code == 200
    assert len(a_res.json()["agents"]) >= 4


def test_auth_login_success():
    """Verify POST /auth/login returns token and profile for valid faculty credentials."""
    res = client.post("/auth/login", json={
        "email": "dr.raman@academics.edu",
        "password": "faculty2026"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["token"].startswith("inst-auth-")
    assert data["user"]["email"] == "dr.raman@academics.edu"
    assert data["user"]["role"] == "FACULTY_ADVISOR"
    assert data["user"]["name"] == "Dr. K. Raman"


def test_auth_login_invalid_credentials():
    """Verify POST /auth/login rejects invalid credentials with 401."""
    res = client.post("/auth/login", json={
        "email": "dr.raman@academics.edu",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_auth_me_and_logout():
    """Verify GET /auth/me with Bearer token and POST /auth/logout."""
    # 1. Login
    login_res = client.post("/auth/login", json={
        "email": "chair@academics.edu",
        "password": "admin2026"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # 2. Check /auth/me with token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["role"] == "DEPARTMENT_CHAIR"
    assert me_data["user"]["name"] == "Dr. S. Mehta"

    # 3. Logout
    logout_res = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # 4. Check /auth/me after logout
    after_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert after_res.status_code == 200
    assert after_res.json()["authenticated"] is False


