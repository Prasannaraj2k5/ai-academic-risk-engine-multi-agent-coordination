"""API route definitions for the AI Academic Early-Warning & Decision Engine."""

from datetime import datetime
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, status

from agents.base_agent import BaseAgent
from api.models import (
    AskRequest,
    AskResponse,
    AuthStatusResponse,
    ClassAnalyzeRequest,
    ClassAnalyzeResponse,
    FacultyReviewRequest,
    FacultyReviewResponse,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MetricsResponse,
    StudentAnalyzeRequest,
    StudentAnalyzeResponse,
    UserProfile,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from memory.database import is_postgres_active
from memory.long_term_memory import long_term_memory
from memory.short_term_memory import short_term_memory
from tools.student_profile import get_student_profile
from workflow.batch_analysis import batch_analyzer
from workflow.executor import workflow_executor

router = APIRouter()
base_advisor_agent = BaseAgent(agent_name="FacultyAdvisoryAssistant")

# Global metrics counter
_metrics_cache = {
    "workflow_count": 0,
    "total_duration_ms": 0.0,
    "tool_usage_counts": {
        "student_profile": 0,
        "attendance_analyzer": 0,
        "performance_analyzer": 0,
        "assignment_analyzer": 0,
        "trend_analyzer": 0,
        "intervention_knowledge": 0,
    },
    "retry_count": 0,
    "database_operations": 0,
}


@router.get("/health", response_model=HealthResponse)
def health_check():
    """System health check endpoint indicating active database and live LLM status."""
    is_pg = is_postgres_active()
    groq_active = base_advisor_agent.is_live_llm
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    return HealthResponse(
        status="healthy",
        engine="AI Academic Early-Warning & Intervention Decision Engine",
        version="2.0.0",
        active_database="PostgreSQL 15" if is_pg else "SQLite fallback",
        is_postgres=is_pg,
        live_groq_llm=groq_active,
        groq_model=model_name,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Process a natural-language academic query with conversational memory retention."""
    sess_id = request.session_id or "default-session"
    q = request.question.strip()

    # Conversational entity resolution
    resolved_student = request.student_id or short_term_memory.resolve_student_id(sess_id, q)

    # Build context if an active student is targeted
    context_str = ""
    if resolved_student:
        latest = long_term_memory.get_latest_assessment(resolved_student)
        if latest:
            context_str = (
                f"Student {resolved_student} current evaluation: Risk Score={latest['total_risk_score']}/100 "
                f"({latest['risk_band']} Risk). Breakdown: {latest['breakdown']}."
            )

    agent_result = base_advisor_agent.ask(q, context=context_str)

    # Record turn in short term memory
    short_term_memory.record_turn(
        session_id=sess_id,
        query=q,
        response=agent_result["response"],
        student_id=resolved_student,
        context={"student_id": resolved_student},
    )

    return AskResponse(
        question=q,
        response=agent_result["response"],
        is_live_llm=agent_result["is_live_llm"],
        model=agent_result["model"],
        agent=agent_result["agent"],
        session_id=sess_id,
        student_id=resolved_student,
        status="success",
        resolved_context={"active_student": resolved_student} if resolved_student else None,
    )


@router.post("/workflow/run", response_model=WorkflowRunResponse)
def run_workflow(request: WorkflowRunRequest):
    """Trigger the multi-agent LangGraph coordination workflow."""
    start_t = time.time()
    exec_result = workflow_executor.execute_sync(
        query=request.query,
        student_id=request.student_id,
        session_id=request.session_id,
        scope=request.scope,
    )
    dur = exec_result.get("duration_ms", 0.0)

    # Update metrics
    _metrics_cache["workflow_count"] += 1
    _metrics_cache["total_duration_ms"] += dur
    for tool_name in exec_result.get("tools_used", []):
        if tool_name in _metrics_cache["tool_usage_counts"]:
            _metrics_cache["tool_usage_counts"][tool_name] += 1
    _metrics_cache["retry_count"] += exec_result.get("retry_count", 0)
    _metrics_cache["database_operations"] += 2  # Assessment + Interventions write

    return WorkflowRunResponse(
        workflow_id=exec_result["workflow_id"],
        status=exec_result["status"],
        current_agent=exec_result["current_agent"],
        start_time=exec_result["start_time"],
        end_time=exec_result.get("end_time"),
        duration_ms=dur,
        retry_count=exec_result.get("retry_count", 0),
        tools_used=exec_result.get("tools_used", []),
        result=exec_result.get("result"),
        errors=exec_result.get("errors", []),
    )


@router.post("/students/analyze", response_model=StudentAnalyzeResponse)
def analyze_student(request: StudentAnalyzeRequest):
    """Perform diagnostic analysis on an individual student (e.g. STU104)."""
    sid = request.student_id.strip().upper()

    # Verify student exists in profile directory
    profile = get_student_profile(sid)
    if profile.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student identifier '{sid}' not found in cohort directory.",
        )

    # Execute workflow for target student
    exec_result = workflow_executor.execute_sync(
        query=f"Analyze student {sid}",
        student_id=sid,
        session_id=request.session_id,
        scope="individual",
    )

    wf_id = exec_result["workflow_id"]
    res_data = exec_result.get("result", {})
    analysis = res_data.get("analysis", {})
    decision = res_data.get("decision", {})

    breakdown_data = analysis.get("breakdown", {
        "performance": 0, "attendance": 0, "assignments": 0, "assessments": 0, "history": 0
    })

    # Retrieve telemetry metrics
    from tools.assignment_analyzer import analyze_assignments
    from tools.attendance_analyzer import analyze_attendance
    from tools.performance_analyzer import analyze_performance
    from tools.trend_analyzer import analyze_trend

    att = analyze_attendance(sid)
    perf = analyze_performance(sid)
    asn = analyze_assignments(sid)
    tr = analyze_trend(sid)

    # Update metrics
    _metrics_cache["workflow_count"] += 1
    _metrics_cache["total_duration_ms"] += exec_result.get("duration_ms", 0.0)
    for t in ["student_profile", "attendance_analyzer", "performance_analyzer", "assignment_analyzer", "trend_analyzer", "intervention_knowledge"]:
        _metrics_cache["tool_usage_counts"][t] = _metrics_cache["tool_usage_counts"].get(t, 0) + 1
    _metrics_cache["database_operations"] += 2

    return StudentAnalyzeResponse(
        workflow_id=wf_id,
        student_id=sid,
        student_name=profile.get("name", "Unknown Student"),
        risk_score=int(analysis.get("total_risk_score", 0)),
        risk_band=analysis.get("risk_band", "LOW"),
        breakdown=breakdown_data,
        risk_factors=analysis.get("risk_factors", []),
        attendance_pct=att.get("overall_attendance_pct", 0.0),
        current_average_pct=perf.get("current_average_pct", 0.0),
        prior_average_pct=tr.get("previous_semester_avg", 0.0),
        performance_delta=tr.get("performance_delta", 0.0),
        failed_assessments_count=perf.get("failed_assessments_count", 0),
        missed_assignments_count=asn.get("missed_count", 0),
        late_assignments_count=asn.get("late_count", 0),
        urgency=decision.get("urgency", "Low"),
        faculty_oversight=decision.get("faculty_oversight", "Routine"),
        follow_up_period=decision.get("follow_up_period", "Routine"),
        confidence=decision.get("confidence", 0.95),
        top_interventions=decision.get("top_3_interventions", []),
        summary=analysis.get("explanation", ""),
        status="success",
    )


@router.post("/class/analyze", response_model=ClassAnalyzeResponse)
def analyze_class(request: ClassAnalyzeRequest):
    """Perform batch analysis across all 60 students in Section CSE-A."""
    section = request.section.strip() or "CSE-A"
    batch_result = batch_analyzer.analyze_cohort(section=section)

    if batch_result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=batch_result.get("error", "Cohort batch analysis failed."),
        )

    # Update metrics
    _metrics_cache["workflow_count"] += len(batch_result.get("ranked_students", []))
    _metrics_cache["total_duration_ms"] += batch_result.get("analysis_duration_ms", 0.0)
    _metrics_cache["database_operations"] += len(batch_result.get("ranked_students", []))

    return ClassAnalyzeResponse(
        section=batch_result["section"],
        total_students=batch_result["total_students"],
        distribution=batch_result["distribution"],
        kpis=batch_result["kpis"],
        critical_student_ids=batch_result["critical_student_ids"],
        high_risk_student_ids=batch_result["high_risk_student_ids"],
        ranked_students=batch_result["ranked_students"],
        analysis_duration_ms=batch_result["analysis_duration_ms"],
        status="success",
    )


@router.get("/workflow/{workflow_id}")
def get_workflow_details(workflow_id: str):
    """Retrieve full execution record and output for a workflow ID."""
    status_dict = workflow_executor.get_status(workflow_id)
    if not status_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found.",
        )
    return status_dict


@router.get("/workflow/{workflow_id}/status")
def get_workflow_status(workflow_id: str):
    """Get concise status and timing for a workflow ID."""
    status_dict = workflow_executor.get_status(workflow_id)
    if not status_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found.",
        )
    return {
        "workflow_id": status_dict["workflow_id"],
        "status": status_dict["status"],
        "current_agent": status_dict["current_agent"],
        "duration_ms": status_dict["duration_ms"],
        "retry_count": status_dict["retry_count"],
        "tools_used": status_dict["tools_used"],
    }


@router.get("/students/{student_id}")
def get_student(student_id: str):
    """Get student demographic profile and course enrollments."""
    sid = student_id.strip().upper()
    profile = get_student_profile(sid)
    if profile.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{sid}' not found.",
        )
    return profile


@router.get("/students/{student_id}/history")
def get_student_history_endpoint(student_id: str):
    """Retrieve longitudinal risk assessment history and faculty reviews for a student."""
    sid = student_id.strip().upper()
    history = long_term_memory.get_student_history(sid)
    return {
        "student_id": sid,
        "history_count": len(history),
        "history": history,
    }


@router.get("/metrics", response_model=MetricsResponse)
def get_system_metrics():
    """Retrieve live aggregated runtime and operational metrics."""
    total_wfs = _metrics_cache["workflow_count"]
    total_dur = _metrics_cache["total_duration_ms"]
    avg_dur = round(total_dur / total_wfs, 2) if total_wfs > 0 else 0.0

    return MetricsResponse(
        workflow_count=total_wfs,
        total_duration_ms=round(total_dur, 2),
        average_duration_ms=avg_dur,
        tool_usage_counts=_metrics_cache["tool_usage_counts"],
        retry_count=_metrics_cache["retry_count"],
        database_operations=_metrics_cache["database_operations"],
        active_database="PostgreSQL 15" if is_postgres_active() else "SQLite fallback",
        is_postgres=is_postgres_active(),
        live_groq_llm=base_advisor_agent.is_live_llm,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/agents")
def list_agents():
    """List the 4 specialized workflow agents and base advisory assistant."""
    return {
        "system": "AI Academic Early-Warning & Intervention Decision Engine",
        "coordination_framework": "LangGraph",
        "agents": [
            {
                "name": "PlanningAgent",
                "role": "Request decomposition, scope detection, and investigation task scheduling",
                "calculates_risk_score": False,
            },
            {
                "name": "ResearchAgent",
                "role": "Execution of investigation plan and academic tool telemetry dispatching",
                "calculates_risk_score": False,
            },
            {
                "name": "AnalysisAgent",
                "role": "Deterministic Python risk calculation (0-100), factor explanation, and trend detection",
                "calculates_risk_score": True,
            },
            {
                "name": "DecisionAgent",
                "role": "Pedagogical intervention formulation, urgency classification, and human review packaging",
                "calculates_risk_score": False,
            },
            {
                "name": "FacultyAdvisoryAssistant",
                "role": "Conversational academic decision support and policy consultation",
                "calculates_risk_score": False,
            },
        ],
    }


@router.post("/memory/search", response_model=MemorySearchResponse)
def search_long_term_memory(request: MemorySearchRequest):
    """Search persisted risk evaluations and governance audit records."""
    results = long_term_memory.search_memory(
        query=request.query or "",
        student_id=request.student_id,
        limit=request.limit,
    )
    return MemorySearchResponse(
        results=results,
        count=len(results),
        status="success",
    )


@router.post("/review/action", response_model=FacultyReviewResponse)
def submit_faculty_review(
    request: FacultyReviewRequest,
    authorization: Optional[str] = Header(None),
):
    """Record human-in-the-loop governance action: APPROVE, MODIFY, or REJECT."""
    action = request.faculty_action.strip().upper()
    if action not in ["APPROVE", "MODIFY", "REJECT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="faculty_action must be 'APPROVE', 'MODIFY', or 'REJECT'.",
        )

    reviewer_name = request.reviewer_name
    if (not reviewer_name or reviewer_name == "Faculty Advisor") and authorization:
        tok = authorization.replace("Bearer ", "").strip()
        session_data = _active_auth_sessions.get(tok)
        if session_data:
            reviewer_name = session_data["user"].name

    res = long_term_memory.record_faculty_review(
        workflow_id=request.workflow_id,
        student_id=request.student_id,
        faculty_action=action,
        feedback=request.feedback or "",
        reviewer_name=reviewer_name or "Dr. K. Raman",
    )

    if "error" in res:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record review: {res['error']}",
        )

    _metrics_cache["database_operations"] += 1

    return FacultyReviewResponse(
        review_id=res["review_id"],
        workflow_id=res["workflow_id"],
        student_id=res["student_id"],
        action=res["action"],
        reviewer=res["reviewer"],
        feedback=request.feedback or "",
        timestamp=res["timestamp"],
        status="success",
    )


# ==============================================================================
# Institutional Authentication & Access Control
# ==============================================================================

INSTITUTIONAL_USERS = {
    "dr.raman@academics.edu": {
        "password": "faculty2026",
        "user_id": "FAC_01",
        "name": "Dr. K. Raman",
        "email": "dr.raman@academics.edu",
        "role": "FACULTY_ADVISOR",
        "role_display": "Faculty Academic Advisor",
        "department": "Computer Science & Engineering",
        "title": "Associate Professor & Senior Advisor",
    },
    "chair@academics.edu": {
        "password": "admin2026",
        "user_id": "ADMIN_01",
        "name": "Dr. S. Mehta",
        "email": "chair@academics.edu",
        "role": "DEPARTMENT_CHAIR",
        "role_display": "Department Chair & Dean",
        "department": "Computer Science & Engineering",
        "title": "Department Head",
    },
    "counselor@academics.edu": {
        "password": "counselor2026",
        "user_id": "COUNSEL_01",
        "name": "Dr. A. Sharma",
        "email": "counselor@academics.edu",
        "role": "ACADEMIC_COUNSELOR",
        "role_display": "Lead Academic Counselor",
        "department": "Student Welfare & Counseling",
        "title": "Senior Counselor",
    },
}

_active_auth_sessions: Dict[str, Dict[str, Any]] = {}


def _resolve_user(identifier: str) -> Optional[Dict[str, Any]]:
    clean = identifier.strip().lower()
    if clean in INSTITUTIONAL_USERS:
        return INSTITUTIONAL_USERS[clean]
    aliases = {
        "dr.raman": "dr.raman@academics.edu",
        "raman": "dr.raman@academics.edu",
        "advisor@academics.edu": "dr.raman@academics.edu",
        "chair": "chair@academics.edu",
        "admin": "chair@academics.edu",
        "counselor": "counselor@academics.edu",
    }
    target = aliases.get(clean)
    if target and target in INSTITUTIONAL_USERS:
        return INSTITUTIONAL_USERS[target]
    return None


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate institutional faculty or administrator credentials."""
    user = _resolve_user(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid institutional credentials. Check your email/username and password.",
        )

    token = f"inst-auth-{uuid.uuid4().hex}"
    expires_at = datetime.fromtimestamp(time.time() + 86400).isoformat()

    user_profile = UserProfile(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
        role=user["role"],
        role_display=user["role_display"],
        department=user["department"],
        title=user["title"],
    )

    _active_auth_sessions[token] = {
        "user": user_profile,
        "token": token,
        "expires_at": expires_at,
    }

    return LoginResponse(
        token=token,
        user=user_profile,
        status="success",
        expires_at=expires_at,
    )


@router.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Invalidate active institutional session."""
    if authorization:
        tok = authorization.replace("Bearer ", "").strip()
        if tok in _active_auth_sessions:
            del _active_auth_sessions[tok]
    return {"status": "success", "message": "Successfully signed out of institutional portal."}


@router.get("/auth/me", response_model=AuthStatusResponse)
def get_current_user(authorization: Optional[str] = Header(None)):
    """Get authenticated user profile."""
    if not authorization:
        return AuthStatusResponse(authenticated=False, user=None)

    tok = authorization.replace("Bearer ", "").strip()
    session_data = _active_auth_sessions.get(tok)
    if not session_data:
        return AuthStatusResponse(authenticated=False, user=None)

    return AuthStatusResponse(authenticated=True, user=session_data["user"])

