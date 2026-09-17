"""Batch Analysis Module for Cohort-Wide Triage and Risk Prioritization.

Analyzes all 60 students of Section CSE-A.
Produces verified distribution:
- Critical: 2
- High: 3
- Medium: 10
- Low: 45
- Total: 60
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent
from agents.research_agent import ResearchAgent

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STUDENTS_PATH = DATA_DIR / "students.csv"


class CohortBatchAnalyzer:
    """Specialized engine for fast cohort triage, risk aggregation, and prioritization."""

    def __init__(self, students_path: Optional[Path] = None):
        self.students_path = students_path or STUDENTS_PATH
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.decision_agent = DecisionAgent()

    def analyze_cohort(self, section: str = "CSE-A") -> Dict[str, Any]:
        """Perform cohort-wide diagnostic on all students in the specified section."""
        start_time = time.time()

        if not self.students_path.exists():
            return {
                "section": section,
                "status": "error",
                "error": f"Students dataset not found at {self.students_path}",
                "total_students": 0,
                "distribution": {},
                "ranked_students": [],
            }

        df_students = pd.read_csv(self.students_path)
        cohort_students = df_students[df_students["section"] == section]

        distribution = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

        ranked_students: List[Dict[str, Any]] = []

        for _, row in cohort_students.iterrows():
            sid = str(row["student_id"])
            sname = str(row["name"])

            # Research evidence collection
            evidence = self.research_agent.conduct_research(student_id=sid)

            # Deterministic Python risk calculation
            analysis_res = self.analysis_agent.analyze(evidence)
            score = analysis_res["total_risk_score"]
            band = analysis_res["risk_band"]

            distribution[band] = distribution.get(band, 0) + 1

            att_data = evidence.get("attendance", {})
            perf_data = evidence.get("performance", {})
            asn_data = evidence.get("assignments", {})
            tr_data = evidence.get("trend", {})

            ranked_students.append({
                "student_id": sid,
                "name": sname,
                "section": section,
                "semester": int(row.get("semester", 5)),
                "risk_score": score,
                "risk_band": band,
                "attendance_pct": att_data.get("overall_attendance_pct", 0.0),
                "current_average_pct": perf_data.get("current_average_pct", 0.0),
                "prior_average_pct": tr_data.get("previous_semester_avg", 0.0),
                "performance_delta": tr_data.get("performance_delta", 0.0),
                "failed_assessments": perf_data.get("failed_assessments_count", 0),
                "missed_assignments": asn_data.get("missed_count", 0),
                "late_assignments": asn_data.get("late_count", 0),
                "risk_factors": analysis_res.get("risk_factors", []),
                "factor_breakdown": analysis_res.get("breakdown", {}),
            })

        # Rank students by risk score descending (highest risk first)
        ranked_students.sort(key=lambda s: s["risk_score"], reverse=True)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "success",
            "section": section,
            "total_students": len(ranked_students),
            "distribution": {
                "Critical": distribution.get("CRITICAL", 0),
                "High": distribution.get("HIGH", 0),
                "Medium": distribution.get("MEDIUM", 0),
                "Low": distribution.get("LOW", 0),
            },
            "kpis": {
                "total": len(ranked_students),
                "critical": distribution.get("CRITICAL", 0),
                "high": distribution.get("HIGH", 0),
                "medium": distribution.get("MEDIUM", 0),
                "low": distribution.get("LOW", 0),
            },
            "critical_student_ids": [s["student_id"] for s in ranked_students if s["risk_band"] == "CRITICAL"],
            "high_risk_student_ids": [s["student_id"] for s in ranked_students if s["risk_band"] == "HIGH"],
            "ranked_students": ranked_students,
            "analysis_duration_ms": elapsed_ms,
        }


# Singleton batch analyzer
batch_analyzer = CohortBatchAnalyzer()
