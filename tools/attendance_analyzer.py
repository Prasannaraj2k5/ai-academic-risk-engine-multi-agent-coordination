"""Attendance Analyzer Tool.

Analyzes:
- Overall attendance percentage
- Subject-wise attendance breakdown
- Low attendance subjects (< 75%)
- Critical threshold classification:
    * < 66%: Critical attendance
    * 66% - 74.99%: Warning
    * >= 75%: Acceptable
- Attendance deficit calculation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACADEMIC_RECORDS_PATH = DATA_DIR / "academic_records.csv"


class AttendanceAnalyzer:
    """Specialized tool for student attendance risk analysis."""

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
        """Analyze attendance metrics for a specific student."""
        if self._records_df is None or self._records_df.empty:
            self._load_data()

        student_records = self._records_df[self._records_df["student_id"] == student_id]
        if student_records.empty:
            return {
                "student_id": student_id,
                "status": "not_found",
                "error": f"No academic records found for student {student_id}",
                "overall_attendance_pct": 0.0,
                "attendance_status": "Unknown",
                "subjects": [],
                "critical_subjects": [],
                "warning_subjects": [],
                "is_critical": False,
                "is_warning": False,
            }

        subjects: List[Dict[str, Any]] = []
        critical_subjects: List[str] = []
        warning_subjects: List[str] = []
        total_attendance = 0.0

        for _, row in student_records.iterrows():
            att = float(row["attendance_pct"])
            total_attendance += att
            ccode = str(row["course_code"])
            cname = str(row["course_name"])

            if att < 66.0:
                tier = "Critical"
                critical_subjects.append(f"{ccode} ({att}%)")
            elif att < 75.0:
                tier = "Warning"
                warning_subjects.append(f"{ccode} ({att}%)")
            else:
                tier = "Acceptable"

            subjects.append({
                "course_code": ccode,
                "course_name": cname,
                "attendance_pct": att,
                "tier": tier,
            })

        overall_avg = round(total_attendance / len(student_records), 1)

        # Institutional rule thresholds
        if overall_avg < 66.0:
            attendance_status = "Critical"
            is_critical = True
            is_warning = False
        elif overall_avg < 75.0:
            attendance_status = "Warning"
            is_critical = False
            is_warning = True
        else:
            attendance_status = "Acceptable"
            is_critical = False
            is_warning = False

        # Attendance deficit below mandatory 75% threshold
        deficit_pct = round(max(0.0, 75.0 - overall_avg), 1)

        return {
            "student_id": student_id,
            "status": "success",
            "overall_attendance_pct": overall_avg,
            "attendance_status": attendance_status,
            "threshold_rule": "<66%: Critical, 66-74.99%: Warning, >=75%: Acceptable",
            "is_critical": is_critical,
            "is_warning": is_warning,
            "deficit_from_acceptable": deficit_pct,
            "total_courses": len(subjects),
            "critical_courses_count": len(critical_subjects),
            "warning_courses_count": len(warning_subjects),
            "critical_subjects": critical_subjects,
            "warning_subjects": warning_subjects,
            "subject_breakdown": subjects,
        }


def analyze_attendance(student_id: str) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    analyzer = AttendanceAnalyzer()
    return analyzer.analyze(student_id)
