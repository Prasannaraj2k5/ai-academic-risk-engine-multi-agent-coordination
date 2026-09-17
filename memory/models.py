"""SQLAlchemy ORM models for the AI Academic Early-Warning & Decision Engine."""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Student(Base):
    """Student master demographic directory."""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    section = Column(String(20), default="CSE-A")
    semester = Column(Integer, default=5)
    department = Column(String(100), default="Computer Science & Engineering")
    advisor_name = Column(String(100), default="Dr. K. Raman")
    email = Column(String(120), nullable=True)
    prior_semester_avg = Column(Float, default=70.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AcademicRecord(Base):
    """Course-wise marks and attendance records."""

    __tablename__ = "academic_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), nullable=False, index=True)
    course_code = Column(String(20), nullable=False)
    course_name = Column(String(100), nullable=False)
    attendance_pct = Column(Float, default=100.0)
    internal_marks = Column(Float, default=0.0)
    midterm_marks = Column(Float, default=0.0)
    final_marks = Column(Float, default=0.0)
    total_marks = Column(Float, default=0.0)
    passed = Column(Boolean, default=True)


class AssignmentRecord(Base):
    """Coursework submission and punctuality telemetry."""

    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(String(50), nullable=False, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    course_code = Column(String(20), nullable=False)
    assignment_num = Column(Integer, default=1)
    status = Column(String(20), default="submitted")  # submitted, late, missed
    score = Column(Float, default=0.0)
    submission_delay_days = Column(Integer, default=0)
    due_week = Column(Integer, default=1)


class RiskAssessment(Base):
    """Persistent audit trail of deterministic student risk evaluations."""

    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    total_risk_score = Column(Integer, nullable=False)
    risk_band = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    performance_score = Column(Integer, default=0)
    attendance_score = Column(Integer, default=0)
    assignments_score = Column(Integer, default=0)
    assessments_score = Column(Integer, default=0)
    history_score = Column(Integer, default=0)
    factor_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InterventionRecommendation(Base):
    """Prescribed academic interventions linked to workflow executions."""

    __tablename__ = "intervention_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    intervention_id = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    target_factor = Column(String(50), nullable=False)
    urgency = Column(String(30), default="High")
    description = Column(Text, nullable=True)
    duration_weeks = Column(Integer, default=4)
    oversight_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FacultyReview(Base):
    """Human-in-the-loop review audit ledger."""

    __tablename__ = "faculty_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    faculty_action = Column(String(30), nullable=False)  # APPROVED, MODIFIED, REJECTED
    feedback = Column(Text, nullable=True)
    reviewer_name = Column(String(100), default="Faculty Advisor")
    timestamp = Column(DateTime, default=datetime.utcnow)


class WorkflowLog(Base):
    """Observability and execution logs."""

    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    agent_name = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
