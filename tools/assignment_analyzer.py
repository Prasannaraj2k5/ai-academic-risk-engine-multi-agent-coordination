"""Assignment Analyzer Tool.

Analyzes:
- Total coursework assignments assigned
- Submitted count
- Missed assignments count
- Late assignments count
- Overall completion rate
- On-time submission rate
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ASSIGNMENTS_PATH = DATA_DIR / "assignments.csv"


class AssignmentAnalyzer:
    """Specialized tool for student assignment compliance and submission regularity."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or ASSIGNMENTS_PATH
        self._assignments_df = None
        self._load_data()

    def _load_data(self) -> None:
        """Load assignments dataset."""
        if self.data_path.exists():
            self._assignments_df = pd.read_csv(self.data_path)
        else:
            self._assignments_df = pd.DataFrame()

    def analyze(self, student_id: str) -> Dict[str, Any]:
        """Analyze assignment engagement metrics for a specific student."""
        if self._assignments_df is None or self._assignments_df.empty:
            self._load_data()

        student_assignments = self._assignments_df[self._assignments_df["student_id"] == student_id]
        if student_assignments.empty:
            return {
                "student_id": student_id,
                "status": "not_found",
                "error": f"No assignment records found for student {student_id}",
                "total_assignments": 0,
                "submitted_count": 0,
                "missed_count": 0,
                "late_count": 0,
                "completion_rate_pct": 0.0,
                "ontime_rate_pct": 0.0,
            }

        total = len(student_assignments)
        missed = int((student_assignments["status"] == "missed").sum())
        late = int((student_assignments["status"] == "late").sum())
        submitted_ontime = int((student_assignments["status"] == "submitted").sum())

        # Total attempted/completed assignments
        total_completed = submitted_ontime + late
        completion_rate = round((total_completed / total) * 100.0, 1) if total > 0 else 0.0
        ontime_rate = round((submitted_ontime / total) * 100.0, 1) if total > 0 else 0.0

        # Average score on completed work
        completed_scores = student_assignments[student_assignments["status"] != "missed"]["score"]
        avg_score = round(float(completed_scores.mean()), 1) if not completed_scores.empty else 0.0

        return {
            "student_id": student_id,
            "status": "success",
            "total_assignments": total,
            "submitted_count": submitted_ontime,
            "late_count": late,
            "missed_count": missed,
            "total_completed": total_completed,
            "completion_rate_pct": completion_rate,
            "ontime_rate_pct": ontime_rate,
            "average_assignment_score": avg_score,
            "has_missed_assignments": missed > 0,
            "has_late_assignments": late > 0,
            "risk_flag": missed >= 2 or late >= 3,
        }


def analyze_assignments(student_id: str) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    analyzer = AssignmentAnalyzer()
    return analyzer.analyze(student_id)
