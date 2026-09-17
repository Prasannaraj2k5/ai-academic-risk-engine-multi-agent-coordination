"""Pydantic schemas for API request validation and structured responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    engine: str = "AI Academic Early-Warning & Intervention Decision Engine"
    version: str = "2.0.0"
    active_database: str  # "PostgreSQL 15" or "SQLite fallback"
    is_postgres: bool
    live_groq_llm: bool
    groq_model: str
    timestamp: str


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural language academic question or student inquiry")
    session_id: Optional[str] = Field(None, description="Conversational session identifier")
    student_id: Optional[str] = Field(None, description="Optional target student ID")


class AskResponse(BaseModel):
    question: str
    response: str
    is_live_llm: bool
    model: str
    agent: str
    session_id: str
    student_id: Optional[str] = None
    status: str = "success"
    resolved_context: Optional[Dict[str, Any]] = None


class WorkflowRunRequest(BaseModel):
    query: str = Field(..., description="Workflow triggering query")
    student_id: Optional[str] = Field(None, description="Target student identifier (e.g. STU104)")
    session_id: Optional[str] = Field(None, description="Optional conversational session ID")
    scope: Optional[str] = Field("individual", description="'individual' or 'cohort'")


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    status: str
    current_agent: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float
    retry_count: int
    tools_used: List[str]
    result: Optional[Dict[str, Any]] = None
    errors: List[str] = []


class StudentAnalyzeRequest(BaseModel):
    student_id: str = Field(..., description="Student ID to analyze (e.g., STU104)")
    session_id: Optional[str] = Field(None, description="Optional conversational session ID")


class FactorBreakdown(BaseModel):
    performance: int
    attendance: int
    assignments: int
    assessments: int
    history: int


class StudentAnalyzeResponse(BaseModel):
    workflow_id: str
    student_id: str
    student_name: str
    risk_score: int
    risk_band: str  # LOW, MEDIUM, HIGH, CRITICAL
    breakdown: FactorBreakdown
    risk_factors: List[str]
    attendance_pct: float
    current_average_pct: float
    prior_average_pct: float
    performance_delta: float
    failed_assessments_count: int
    missed_assignments_count: int
    late_assignments_count: int
    urgency: str
    faculty_oversight: str
    follow_up_period: str
    confidence: float
    top_interventions: List[Dict[str, Any]]
    summary: str
    status: str = "success"


class ClassAnalyzeRequest(BaseModel):
    section: str = Field("CSE-A", description="Cohort section identifier")


class ClassAnalyzeResponse(BaseModel):
    section: str
    total_students: int
    distribution: Dict[str, int]
    kpis: Dict[str, int]
    critical_student_ids: List[str]
    high_risk_student_ids: List[str]
    ranked_students: List[Dict[str, Any]]
    analysis_duration_ms: float
    status: str = "success"


class FacultyReviewRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID to review")
    student_id: str = Field(..., description="Target student ID")
    faculty_action: str = Field(..., description="'APPROVE', 'MODIFY', or 'REJECT'")
    feedback: Optional[str] = Field("", description="Faculty comments or modified interventions")
    reviewer_name: Optional[str] = Field("Dr. K. Raman", description="Name of reviewing faculty member")


class FacultyReviewResponse(BaseModel):
    review_id: int
    workflow_id: str
    student_id: str
    action: str
    reviewer: str
    feedback: str
    timestamp: str
    status: str = "success"


class MetricsResponse(BaseModel):
    workflow_count: int
    total_duration_ms: float
    average_duration_ms: float
    tool_usage_counts: Dict[str, int]
    retry_count: int
    database_operations: int
    active_database: str
    is_postgres: bool
    live_groq_llm: bool
    groq_model: str
    timestamp: str


class MemorySearchRequest(BaseModel):
    query: Optional[str] = Field("", description="Search term")
    student_id: Optional[str] = Field(None, description="Optional filter by student ID")
    limit: int = Field(10, description="Max results")


class MemorySearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    status: str = "success"


class LoginRequest(BaseModel):
    email: str = Field(..., description="Institutional email or username")
    password: str = Field(..., description="Institutional account password")


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    role: str  # "FACULTY_ADVISOR", "DEPARTMENT_CHAIR", "ACADEMIC_COUNSELOR"
    role_display: str
    department: str
    title: str


class LoginResponse(BaseModel):
    token: str
    user: UserProfile
    status: str = "success"
    expires_at: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserProfile] = None

