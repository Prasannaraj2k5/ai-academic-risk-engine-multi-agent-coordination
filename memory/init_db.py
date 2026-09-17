"""Database Initialization and Seeding Script.

Reads synthetic CSV/JSON files and populates database tables.
Safe and idempotent.
"""

import json
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import text

from memory.database import get_engine, get_session_factory, is_postgres_active
from memory.models import (
    AcademicRecord,
    AssignmentRecord,
    Base,
    FacultyReview,
    InterventionRecommendation,
    RiskAssessment,
    Student,
    WorkflowLog,
)

logger = logging.getLogger("academic_risk.init_db")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def seed_database():
    """Create all tables and seed synthetic data."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    SessionMaker = get_session_factory()
    db = SessionMaker()

    try:
        # Check if already seeded
        student_count = db.query(Student).count()
        if student_count >= 60:
            print(f"Database already contains {student_count} students. Skipping re-seed.")
            return

        # 1. Seed Students
        students_csv = DATA_DIR / "students.csv"
        if students_csv.exists():
            df_students = pd.read_csv(students_csv)
            for _, r in df_students.iterrows():
                st = Student(
                    student_id=str(r["student_id"]),
                    name=str(r["name"]),
                    section=str(r.get("section", "CSE-A")),
                    semester=int(r.get("semester", 5)),
                    department=str(r.get("department", "Computer Science & Engineering")),
                    advisor_name=str(r.get("advisor_name", "Dr. K. Raman")),
                    email=str(r.get("email", f"{r['student_id'].lower()}@academics.edu")),
                    prior_semester_avg=float(r.get("prior_semester_avg", 70.0)),
                )
                db.add(st)
            db.commit()
            print(f"Seeded {len(df_students)} students.")

        # 2. Seed Academic Records
        records_csv = DATA_DIR / "academic_records.csv"
        if records_csv.exists():
            df_records = pd.read_csv(records_csv)
            for _, r in df_records.iterrows():
                ar = AcademicRecord(
                    student_id=str(r["student_id"]),
                    course_code=str(r["course_code"]),
                    course_name=str(r["course_name"]),
                    attendance_pct=float(r["attendance_pct"]),
                    internal_marks=float(r.get("internal_marks", 0.0)),
                    midterm_marks=float(r.get("midterm_marks", 0.0)),
                    final_marks=float(r.get("final_assessment_marks", 0.0)),
                    total_marks=float(r["total_marks"]),
                    passed=bool(r.get("passed", True)),
                )
                db.add(ar)
            db.commit()
            print(f"Seeded {len(df_records)} academic records.")

        # 3. Seed Assignment Records
        assignments_csv = DATA_DIR / "assignments.csv"
        if assignments_csv.exists():
            df_assignments = pd.read_csv(assignments_csv)
            for _, r in df_assignments.iterrows():
                asn = AssignmentRecord(
                    assignment_id=str(r["assignment_id"]),
                    student_id=str(r["student_id"]),
                    course_code=str(r["course_code"]),
                    assignment_num=int(r["assignment_num"]),
                    status=str(r["status"]),
                    score=float(r.get("score", 0.0)),
                    submission_delay_days=int(r.get("submission_delay_days", 0)),
                    due_week=int(r.get("due_week", 1)),
                )
                db.add(asn)
            db.commit()
            print(f"Seeded {len(df_assignments)} assignment records.")

        # 4. Seed Historical Interventions
        history_json = DATA_DIR / "sample_history.json"
        if history_json.exists():
            with open(history_json, "r", encoding="utf-8") as f:
                history_data = json.load(f)
            for h in history_data:
                ra = RiskAssessment(
                    workflow_id=f"wf-hist-{h['student_id']}-sem{h['semester']}",
                    student_id=h["student_id"],
                    total_risk_score=h.get("recorded_risk_score", 50),
                    risk_band=h.get("risk_band", "MEDIUM"),
                    performance_score=20,
                    attendance_score=15,
                    assignments_score=10,
                    assessments_score=5,
                    history_score=h.get("history_contribution_score", 5),
                    factor_breakdown={"historical_flags": h.get("historical_flags", [])},
                )
                db.add(ra)
            db.commit()
            print(f"Seeded {len(history_data)} historical assessments.")

        print(f"Database initialization complete (PostgreSQL active: {is_postgres_active()}).")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
