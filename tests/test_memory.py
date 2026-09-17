"""Unit tests for Short-Term Memory and Long-Term Database Persistence."""

import pytest
from memory.database import is_postgres_active
from memory.long_term_memory import long_term_memory
from memory.short_term_memory import short_term_memory


def test_short_term_conversational_continuity():
    """Verify session tracking and entity continuity across follow-up queries."""
    session_id = "test-session-continuity"
    short_term_memory.clear_session(session_id)

    # Turn 1: Explicit target query
    resolved_1 = short_term_memory.resolve_student_id(session_id, "Please analyze STU104")
    assert resolved_1 == "STU104"
    
    short_term_memory.record_turn(
        session_id=session_id,
        query="Please analyze STU104",
        response="STU104 analyzed with Critical Risk (89/100).",
        student_id="STU104",
    )

    # Turn 2: Contextual follow-up query without mentioning student ID
    resolved_2 = short_term_memory.resolve_student_id(session_id, "What about attendance?")
    assert resolved_2 == "STU104"  # Correctly resolved to STU104 from session context!

    ctx = short_term_memory.get_session_context(session_id)
    assert ctx["active_student"] == "STU104"
    assert ctx["turns_count"] == 1


def test_long_term_memory_persistence():
    """Verify storing and querying risk assessments, interventions, and reviews."""
    wf_id = "wf-test-persistence-001"
    student_id = "STU104"

    # 1. Save Risk Assessment
    saved_ra = long_term_memory.save_risk_assessment(
        workflow_id=wf_id,
        student_id=student_id,
        total_risk_score=89,
        risk_band="CRITICAL",
        breakdown={"performance": 30, "attendance": 25, "assignments": 17, "assessments": 10, "history": 7},
    )
    assert saved_ra["risk_score"] == 89
    assert saved_ra["risk_band"] == "CRITICAL"

    # 2. Save Interventions
    saved_intv = long_term_memory.save_interventions(
        workflow_id=wf_id,
        student_id=student_id,
        interventions=[
            {"id": "INT_01", "title": "Attendance Plan", "target_factor": "Attendance", "urgency": "High"}
        ],
    )
    assert len(saved_intv) == 1

    # 3. Save Faculty Review
    saved_review = long_term_memory.record_faculty_review(
        workflow_id=wf_id,
        student_id=student_id,
        faculty_action="APPROVE",
        feedback="Approved structured attendance plan.",
        reviewer_name="Dr. K. Raman",
    )
    assert saved_review["action"] == "APPROVE"
    assert saved_review["reviewer"] == "Dr. K. Raman"

    # 4. Query student history
    history = long_term_memory.get_student_history(student_id)
    assert len(history) >= 1
    found = any(h["workflow_id"] == wf_id for h in history)
    assert found is True
