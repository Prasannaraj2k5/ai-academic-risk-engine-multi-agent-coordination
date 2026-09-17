"""Unit tests for the 6 specialized academic decision tools."""

import pytest
from tools.attendance_analyzer import AttendanceAnalyzer, analyze_attendance
from tools.performance_analyzer import PerformanceAnalyzer, analyze_performance
from tools.assignment_analyzer import AssignmentAnalyzer, analyze_assignments
from tools.trend_analyzer import TrendAnalyzer, analyze_trend
from tools.student_profile import StudentProfileTool, get_student_profile
from tools.intervention_knowledge import InterventionKnowledgeBase, recommend_interventions


def test_attendance_analyzer():
    """Verify attendance metrics, critical/warning thresholds, and STU104 data."""
    att = analyze_attendance("STU104")
    assert att["status"] == "success"
    assert att["overall_attendance_pct"] == 68.0
    assert att["attendance_status"] == "Warning"
    assert att["is_warning"] is True
    assert att["critical_courses_count"] == 2  # CS301 (65%) and CS302 (62%)
    assert len(att["subject_breakdown"]) == 5


def test_performance_analyzer():
    """Verify performance metrics, current average, and failed assessments."""
    perf = analyze_performance("STU104")
    assert perf["status"] == "success"
    assert perf["current_average_pct"] == 54.7
    assert perf["failed_assessments_count"] == 2
    assert perf["has_failed_assessments"] is True
    assert len(perf["failed_courses"]) == 2
    failed_codes = [c["course_code"] for c in perf["failed_courses"]]
    assert "CS301" in failed_codes
    assert "CS302" in failed_codes


def test_assignment_analyzer():
    """Verify assignment submission telemetry, completion rate, and delay tracking."""
    asn = analyze_assignments("STU104")
    assert asn["status"] == "success"
    assert asn["total_assignments"] == 20
    assert asn["missed_count"] == 2
    assert asn["late_count"] == 4
    assert asn["submitted_count"] == 14
    assert asn["completion_rate_pct"] == 90.0
    assert asn["has_missed_assignments"] is True
    assert asn["has_late_assignments"] is True


def test_trend_analyzer():
    """Verify semester deltas, trajectory classification, and significant decline flag."""
    tr = analyze_trend("STU104")
    assert tr["status"] == "success"
    assert tr["previous_semester_avg"] == 74.0
    assert tr["current_semester_avg"] == 54.7
    assert tr["performance_delta"] == -19.3
    assert tr["is_declining"] is True
    assert tr["is_significant_decline"] is True


def test_student_profile_tool():
    """Verify unified student profile retrieval."""
    prof = get_student_profile("STU104")
    assert prof["status"] == "success"
    assert prof["student_id"] == "STU104"
    assert prof["name"] == "Rohan Verma"
    assert prof["section"] == "CSE-A"
    assert prof["semester"] == 5
    assert prof["enrolled_courses_count"] == 5


def test_intervention_knowledge_base():
    """Verify matching of academic risk triggers to intervention playbook."""
    triggers = [
        "Low attendance",
        "Significant performance decline",
        "Multiple failed assessments",
        "Missed assignments",
    ]
    intv = recommend_interventions(triggers)
    assert intv["status"] == "success"
    assert intv["matched_interventions_count"] >= 3
    assert len(intv["top_3_recommendations"]) == 3
    
    titles = [i["title"] for i in intv["top_3_recommendations"]]
    assert any("Attendance" in t or "Counseling" in t for t in titles)
    assert any("Tutorial" in t or "Mentoring" in t for t in titles)
