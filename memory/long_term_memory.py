"""Long-Term Memory System using SQLAlchemy with PostgreSQL primary and SQLite fallback.

Persists:
- Student Risk Assessments (Scores, bands, breakdowns)
- Interventions Prescribed & Status
- Faculty Human-in-the-Loop Reviews (Approve/Modify/Reject)
- Workflow Audit Logs
- Historical Trajectories
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from memory.database import get_session_factory
from memory.models import (
    FacultyReview,
    InterventionRecommendation,
    RiskAssessment,
    Student,
    WorkflowLog,
)

logger = logging.getLogger("academic_risk.long_term_memory")


class LongTermMemory:
    """Persistent storage repository for institutional records and governance."""

    def __init__(self):
        self.session_factory = get_session_factory()

    def _get_session(self) -> Session:
        return self.session_factory()

    def save_risk_assessment(
        self,
        workflow_id: str,
        student_id: str,
        total_risk_score: int,
        risk_band: str,
        breakdown: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist a completed deterministic risk evaluation."""
        db = self._get_session()
        try:
            ra = RiskAssessment(
                workflow_id=workflow_id,
                student_id=student_id,
                total_risk_score=total_risk_score,
                risk_band=risk_band,
                performance_score=breakdown.get("performance", 0),
                attendance_score=breakdown.get("attendance", 0),
                assignments_score=breakdown.get("assignments", 0),
                assessments_score=breakdown.get("assessments", 0),
                history_score=breakdown.get("history", 0),
                factor_breakdown=breakdown,
                created_at=datetime.utcnow(),
            )
            db.add(ra)
            db.commit()
            db.refresh(ra)
            return {
                "id": ra.id,
                "workflow_id": ra.workflow_id,
                "student_id": ra.student_id,
                "risk_score": ra.total_risk_score,
                "risk_band": ra.risk_band,
            }
        except Exception as e:
            db.rollback()
            logger.error("Failed to save risk assessment: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    def save_interventions(
        self,
        workflow_id: str,
        student_id: str,
        interventions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Persist recommended interventions for a student."""
        db = self._get_session()
        saved = []
        try:
            for item in interventions:
                rec = InterventionRecommendation(
                    workflow_id=workflow_id,
                    student_id=student_id,
                    intervention_id=item.get("id", "INT_GEN"),
                    title=item.get("title", "Intervention Plan"),
                    target_factor=item.get("target_factor", "General"),
                    urgency=item.get("urgency", "Medium"),
                    description=item.get("description", ""),
                    duration_weeks=item.get("duration_weeks", 4),
                    oversight_required=item.get("oversight_required", True),
                    created_at=datetime.utcnow(),
                )
                db.add(rec)
                saved.append({
                    "id": rec.intervention_id,
                    "title": rec.title,
                    "urgency": rec.urgency,
                })
            db.commit()
            return saved
        except Exception as e:
            db.rollback()
            logger.error("Failed to save interventions: %s", e)
            return []
        finally:
            db.close()

    def record_faculty_review(
        self,
        workflow_id: str,
        student_id: str,
        faculty_action: str,  # APPROVED, MODIFIED, REJECTED
        feedback: str = "",
        reviewer_name: str = "Faculty Advisor",
    ) -> Dict[str, Any]:
        """Record human-in-the-loop decision."""
        db = self._get_session()
        try:
            fr = FacultyReview(
                workflow_id=workflow_id,
                student_id=student_id,
                faculty_action=faculty_action.upper(),
                feedback=feedback,
                reviewer_name=reviewer_name,
                timestamp=datetime.utcnow(),
            )
            db.add(fr)
            db.commit()
            db.refresh(fr)
            return {
                "review_id": fr.id,
                "workflow_id": fr.workflow_id,
                "student_id": fr.student_id,
                "action": fr.faculty_action,
                "reviewer": fr.reviewer_name,
                "timestamp": fr.timestamp.isoformat(),
            }
        except Exception as e:
            db.rollback()
            logger.error("Failed to record faculty review: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    def log_event(
        self,
        workflow_id: str,
        event_type: str,
        agent_name: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """Log observability event for a workflow."""
        db = self._get_session()
        try:
            log = WorkflowLog(
                workflow_id=workflow_id,
                event_type=event_type,
                agent_name=agent_name,
                details=details,
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.debug("Logging failed silently: %s", e)
        finally:
            db.close()

    def get_student_history(self, student_id: str) -> List[Dict[str, Any]]:
        """Retrieve longitudinal risk history and reviews for a student."""
        db = self._get_session()
        try:
            assessments = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.student_id == student_id)
                .order_by(RiskAssessment.created_at.desc())
                .all()
            )
            reviews = (
                db.query(FacultyReview)
                .filter(FacultyReview.student_id == student_id)
                .order_by(FacultyReview.timestamp.desc())
                .all()
            )

            return [
                {
                    "assessment_id": a.id,
                    "workflow_id": a.workflow_id,
                    "total_risk_score": a.total_risk_score,
                    "risk_band": a.risk_band,
                    "breakdown": {
                        "performance": a.performance_score,
                        "attendance": a.attendance_score,
                        "assignments": a.assignments_score,
                        "assessments": a.assessments_score,
                        "history": a.history_score,
                    },
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "reviews": [
                        {
                            "action": r.faculty_action,
                            "feedback": r.feedback,
                            "reviewer": r.reviewer_name,
                            "timestamp": r.timestamp.isoformat(),
                        }
                        for r in reviews
                        if r.workflow_id == a.workflow_id
                    ],
                }
                for a in assessments
            ]
        finally:
            db.close()

    def get_latest_assessment(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the most recent risk score record for a student."""
        history = self.get_student_history(student_id)
        return history[0] if history else None

    def search_memory(
        self,
        query: str,
        student_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search historical evaluations and faculty actions."""
        db = self._get_session()
        try:
            q = db.query(RiskAssessment)
            if student_id:
                q = q.filter(RiskAssessment.student_id == student_id)
            records = q.order_by(RiskAssessment.created_at.desc()).limit(limit).all()
            return [
                {
                    "student_id": r.student_id,
                    "workflow_id": r.workflow_id,
                    "risk_score": r.total_risk_score,
                    "risk_band": r.risk_band,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        finally:
            db.close()


# Singleton instance
long_term_memory = LongTermMemory()
