"""Performance Analyzer Tool.

Analyzes:
- Current average marks across all subjects
- Subject-wise marks breakdown
- Failed assessments (marks below institutional passing bar of 50%)
- Weak courses (marks below 60%)
- Pass/fail assessment counts
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACADEMIC_RECORDS_PATH = DATA_DIR / "academic_records.csv"


class PerformanceAnalyzer:
    """Specialized tool for student academic performance evaluation."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or ACADEMIC_RECORDS_PATH
        self._records_df = None
        self._load_data()

    def _load_data(self) -> None:
        """Load academic records dataset."""
        if self.data_path.exists():
            self._records_df = pd.read_csv(self.data_path)
        else:
            self._records_df = pd.DataFrame()

    def analyze(self, student_id: str) -> Dict[str, Any]:
        """Analyze performance and assessment results for a specific student."""
        if self._records_df is None or self._records_df.empty:
            self._load_data()

        student_records = self._records_df[self._records_df["student_id"] == student_id]
        if student_records.empty:
            return {
                "student_id": student_id,
                "status": "not_found",
                "error": f"No academic records found for student {student_id}",
                "current_average_pct": 0.0,
                "failed_assessments_count": 0,
                "failed_courses": [],
                "weak_courses": [],
                "courses": [],
            }

        total_marks = 0.0
        courses: List[Dict[str, Any]] = []
        failed_courses: List[Dict[str, Any]] = []
        weak_courses: List[Dict[str, Any]] = []

        for _, row in student_records.iterrows():
            m = float(row["total_marks"])
            total_marks += m
            ccode = str(row["course_code"])
            cname = str(row["course_name"])
            is_passed = bool(m >= 50.0)

            c_data = {
                "course_code": ccode,
                "course_name": cname,
                "total_marks": m,
                "internal_marks": float(row.get("internal_marks", 0.0)),
                "midterm_marks": float(row.get("midterm_marks", 0.0)),
                "final_marks": float(row.get("final_assessment_marks", 0.0)),
                "passed": is_passed,
            }
            courses.append(c_data)

            if not is_passed:
                failed_courses.append({
                    "course_code": ccode,
                    "course_name": cname,
                    "marks": m,
                    "deficit": round(50.0 - m, 1),
                })
            elif m < 60.0:
                weak_courses.append({
                    "course_code": ccode,
                    "course_name": cname,
                    "marks": m,
                })

        current_avg = round(total_marks / len(student_records), 1)

        return {
            "student_id": student_id,
            "status": "success",
            "current_average_pct": current_avg,
            "total_courses": len(courses),
            "passed_courses_count": len(courses) - len(failed_courses),
            "failed_assessments_count": len(failed_courses),
            "failed_courses": failed_courses,
            "weak_courses_count": len(weak_courses),
            "weak_courses": weak_courses,
            "has_failed_assessments": len(failed_courses) > 0,
            "course_details": courses,
        }


def analyze_performance(student_id: str) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    analyzer = PerformanceAnalyzer()
    return analyzer.analyze(student_id)
