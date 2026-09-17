"""Student Profile Tool.

Returns unified student profile:
- Student ID, Full Name, Section, Semester, Department
- Faculty Academic Advisor
- Enrolled courses list
- Overall academic standing summary
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STUDENTS_PATH = DATA_DIR / "students.csv"
ACADEMIC_RECORDS_PATH = DATA_DIR / "academic_records.csv"


class StudentProfileTool:
    """Specialized tool for retrieving cohesive demographic and academic profile."""

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
        """Load datasets."""
        if self.students_path.exists():
            self._students_df = pd.read_csv(self.students_path)
        else:
            self._students_df = pd.DataFrame()

        if self.records_path.exists():
            self._records_df = pd.read_csv(self.records_path)
        else:
            self._records_df = pd.DataFrame()

    def get_profile(self, student_id: str) -> Dict[str, Any]:
        """Fetch unified profile for a given student ID."""
        if self._students_df is None or self._students_df.empty:
            self._load_data()

        student_row = self._students_df[self._students_df["student_id"] == student_id]
        if student_row.empty:
            return {
                "student_id": student_id,
                "status": "not_found",
                "error": f"Student {student_id} not found",
            }

        s = student_row.iloc[0]

        # Enrolled courses
        enrolled_courses: List[Dict[str, Any]] = []
        if self._records_df is not None and not self._records_df.empty:
            st_records = self._records_df[self._records_df["student_id"] == student_id]
            for _, r in st_records.iterrows():
                enrolled_courses.append({
                    "course_code": str(r["course_code"]),
                    "course_name": str(r["course_name"]),
                    "attendance_pct": float(r["attendance_pct"]),
                    "total_marks": float(r["total_marks"]),
                    "passed": bool(r.get("passed", True)),
                })

        return {
            "student_id": student_id,
            "status": "success",
            "name": str(s.get("name", "Unknown")),
            "section": str(s.get("section", "CSE-A")),
            "semester": int(s.get("semester", 5)),
            "department": str(s.get("department", "Computer Science & Engineering")),
            "advisor_name": str(s.get("advisor_name", "Dr. K. Raman")),
            "email": str(s.get("email", f"{student_id.lower()}@academics.edu")),
            "prior_semester_avg": float(s.get("prior_semester_avg", 0.0)),
            "enrolled_courses_count": len(enrolled_courses),
            "enrolled_courses": enrolled_courses,
        }


def get_student_profile(student_id: str) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    tool = StudentProfileTool()
    return tool.get_profile(student_id)
