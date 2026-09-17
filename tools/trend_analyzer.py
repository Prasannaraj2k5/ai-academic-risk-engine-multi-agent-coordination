"""Trend Analyzer Tool.

Analyzes:
- Prior semester average performance
- Current semester average performance
- Numerical delta (Current - Prior)
- Performance trajectory (improving, stable, declining)
- Significant decline flag (drop exceeding 15%)
- Longitudinal risk velocity
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STUDENTS_PATH = DATA_DIR / "students.csv"
ACADEMIC_RECORDS_PATH = DATA_DIR / "academic_records.csv"


class TrendAnalyzer:
    """Specialized tool for longitudinal semester-over-semester trend analysis."""

    def __init__(
        self,
        students_path: Optional[Path] = None,
        records_path: Optional[Path] = None,
    ):
        self.students_path = students_path or STUDENTS_PATH
        self.records_path = records_path or ACADEMIC_RECORDS_PATH
        self._students_df = None
        self._records_df = None
        self._load_data()

    def _load_data(self) -> None:
        """Load student and academic records datasets."""
        if self.students_path.exists():
            self._students_df = pd.read_csv(self.students_path)
        else:
            self._students_df = pd.DataFrame()

        if self.records_path.exists():
            self._records_df = pd.read_csv(self.records_path)
        else:
            self._records_df = pd.DataFrame()

    def analyze(self, student_id: str) -> Dict[str, Any]:
        """Compute semester-over-semester trend deltas for a student."""
        if self._students_df is None or self._students_df.empty:
            self._load_data()

        student_row = self._students_df[self._students_df["student_id"] == student_id]
        if student_row.empty:
            return {
                "student_id": student_id,
                "status": "not_found",
                "error": f"Student {student_id} not found in student directory",
                "previous_semester_avg": 0.0,
                "current_semester_avg": 0.0,
                "performance_delta": 0.0,
                "is_declining": False,
                "is_significant_decline": False,
            }

        prior_avg = float(student_row.iloc[0].get("prior_semester_avg", 0.0))

        # Current semester average
        student_records = self._records_df[self._records_df["student_id"] == student_id]
        if student_records.empty:
            current_avg = 0.0
            current_att = 0.0
        else:
            current_avg = round(float(student_records["total_marks"].mean()), 1)
            current_att = round(float(student_records["attendance_pct"].mean()), 1)

        # Numerical delta
        perf_delta = round(current_avg - prior_avg, 1)
        is_declining = perf_delta < 0
        # Significant decline threshold: drop > 15 percentage points (i.e. delta < -15.0)
        is_significant_decline = perf_delta < -15.0

        if perf_delta > 5.0:
            trajectory = "Strong Improvement"
        elif perf_delta >= 0.0:
            trajectory = "Stable"
        elif perf_delta > -15.0:
            trajectory = "Moderate Decline"
        else:
            trajectory = "Severe Decline"

        return {
            "student_id": student_id,
            "status": "success",
            "previous_semester_avg": prior_avg,
            "current_semester_avg": current_avg,
            "performance_delta": perf_delta,
            "current_attendance_avg": current_att,
            "trajectory": trajectory,
            "is_declining": is_declining,
            "is_significant_decline": is_significant_decline,
            "critical_warning_threshold": -15.0,
            "trajectory_summary": (
                f"Student shifted from {prior_avg}% to {current_avg}% "
                f"({'+' if perf_delta > 0 else ''}{perf_delta}% delta). "
                f"Classification: {trajectory}."
            ),
        }


def analyze_trend(student_id: str) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    analyzer = TrendAnalyzer()
    return analyzer.analyze(student_id)
