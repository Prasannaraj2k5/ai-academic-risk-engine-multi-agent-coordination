"""End-to-End Live HTTP Verification Script."""

import httpx

base = "http://127.0.0.1:8000"

print("\n--- 1. Root / Dashboard ---")
root = httpx.get(f"{base}/")
print("Status:", root.status_code)
print("Contains 'Decision Engine':", "Decision Engine" in root.text)
assert root.status_code == 200

print("\n--- 2. Health Endpoint ---")
health = httpx.get(f"{base}/health").json()
print("Status:", health["status"])
print("Database:", health["active_database"])
print("Live Groq LLM:", health["live_groq_llm"])
assert health["status"] == "healthy"

print("\n--- 3. Ask Academic Question ---")
ask1 = httpx.post(f"{base}/ask", json={"question": "What is academic risk?"}).json()
print("Status:", ask1["status"])
print("Response preview:", ask1["response"][:120], "...")
assert ask1["status"] == "success"

print("\n--- 4. Analyze STU104 ---")
sess = "e2e-demo-session"
stu = httpx.post(f"{base}/students/analyze", json={"student_id": "STU104", "session_id": sess}).json()
wf_id = stu["workflow_id"]
print("Workflow ID:", wf_id)
print("Student:", stu["student_id"], f"({stu['student_name']})")
print("Risk Score:", stu["risk_score"], "/ 100")
print("Risk Band:", stu["risk_band"])
print("Attendance:", stu["attendance_pct"], "%")
print("Current Avg:", stu["current_average_pct"], "%")
print("Prior Avg:", stu["prior_average_pct"], "%")
print("Delta:", stu["performance_delta"], "%")
print("Breakdown:", stu["breakdown"])
print("Urgency:", stu["urgency"])
print("Top Interventions:", [i["title"] for i in stu["top_interventions"]])
assert stu["risk_score"] == 89
assert stu["risk_band"] == "CRITICAL"
assert stu["breakdown"] == {"performance": 30, "attendance": 25, "assignments": 17, "assessments": 10, "history": 7}

print("\n--- 5. Conversational Follow-Up ('What about attendance?') ---")
ask2 = httpx.post(f"{base}/ask", json={"question": "What about attendance?", "session_id": sess}).json()
print("Status:", ask2["status"])
print("Resolved Student in Context:", ask2.get("student_id"))
print("Response preview:", ask2["response"][:120], "...")
assert ask2["student_id"] == "STU104"

print("\n--- 6. Cohort Analysis (CSE-A) ---")
cohort = httpx.post(f"{base}/class/analyze", json={"section": "CSE-A"}).json()
print("Total Students:", cohort["total_students"])
print("Distribution:", cohort["distribution"])
print("Critical IDs:", cohort["critical_student_ids"])
print("High IDs:", cohort["high_risk_student_ids"])
assert cohort["total_students"] == 60
assert cohort["distribution"] == {"Critical": 2, "High": 3, "Medium": 10, "Low": 45}

print("\n--- 7. Faculty Review Governance Action ---")
rev = httpx.post(f"{base}/review/action", json={
    "workflow_id": wf_id,
    "student_id": "STU104",
    "faculty_action": "APPROVE",
    "feedback": "Approved structured attendance improvement plan and remedial tutorials",
    "reviewer_name": "Dr. K. Raman"
}).json()
print("Review Action:", rev["action"])
print("Reviewer:", rev["reviewer"])
print("Timestamp:", rev["timestamp"])
assert rev["action"] == "APPROVE"

print("\n--- 8. Workflow Status Retrieval ---")
wf_stat = httpx.get(f"{base}/workflow/{wf_id}/status").json()
print("Workflow Status:", wf_stat["status"])
print("Current Agent:", wf_stat["current_agent"])
print("Duration:", wf_stat["duration_ms"], "ms")
assert wf_stat["status"] == "COMPLETED"

print("\n--- 9. System Metrics Telemetry ---")
m = httpx.get(f"{base}/metrics").json()
print("Workflows Executed:", m["workflow_count"])
print("Database Operations:", m["database_operations"])
print("Active Database:", m["active_database"])
assert m["workflow_count"] > 0

print("\n==========================================")
print("ALL LIVE E2E VERIFICATIONS PASSED SUCCESSFULLY!")
print("==========================================")
