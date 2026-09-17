"""Intervention Knowledge Base Tool.

Maps academic risk factors to appropriate educational interventions:
- Low attendance -> Structured Attendance Improvement Plan
- Critical attendance -> Mandatory Faculty Counseling
- Performance decline -> Academic Mentoring Program
- Failed assessments -> Remedial Subject Tutorials
- Missed assignments -> Assignment Recovery Plan
- Prior academic warning -> Academic Probation Monitoring Agreement
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INTERVENTIONS_PATH = DATA_DIR / "interventions.json"


class InterventionKnowledgeBase:
    """Specialized knowledge tool matching diagnosed risk triggers with pedagogical actions."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or INTERVENTIONS_PATH
        self._catalog: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load curated intervention catalog."""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._catalog = data.get("interventions", [])
            except Exception:
                self._catalog = []
        else:
            self._catalog = self._default_catalog()

    def _default_catalog(self) -> List[Dict[str, Any]]:
        """Fallback catalog in case JSON file is inaccessible."""
        return [
            {
                "id": "INT_ATT_01",
                "trigger": "Low attendance",
                "title": "Structured Attendance Improvement Plan",
                "description": "Establish a mandatory daily attendance verification protocol with faculty advisor check-ins every Monday.",
                "target_factor": "Attendance",
                "urgency": "High",
                "duration_weeks": 4,
                "oversight_required": True,
            },
            {
                "id": "INT_ATT_02",
                "trigger": "Critical attendance",
                "title": "Mandatory Faculty Counseling",
                "description": "One-on-one counseling with Department Chair and Academic Counselor to evaluate attendance barriers and formulate remediation.",
                "target_factor": "Attendance",
                "urgency": "Immediate",
                "duration_weeks": 2,
                "oversight_required": True,
            },
            {
                "id": "INT_PERF_01",
                "trigger": "Performance decline",
                "title": "Academic Mentoring Program",
                "description": "Pair student with a senior faculty mentor to conduct bi-weekly study progress diagnostics and concept clarification.",
                "target_factor": "Performance",
                "urgency": "Medium",
                "duration_weeks": 6,
                "oversight_required": True,
            },
            {
                "id": "INT_PERF_02",
                "trigger": "Failed assessments",
                "title": "Remedial Subject Tutorials",
                "description": "Enroll student into specialized remedial tutorial cohorts for subjects scoring below passing threshold (<50%).",
                "target_factor": "Assessments",
                "urgency": "Immediate",
                "duration_weeks": 6,
                "oversight_required": True,
            },
            {
                "id": "INT_ASN_01",
                "trigger": "Missed assignments",
                "title": "Assignment Recovery Plan",
                "description": "Provide a structured 14-day schedule for submission of missed coursework and late deliverables with guided office hours.",
                "target_factor": "Assignments",
                "urgency": "High",
                "duration_weeks": 3,
                "oversight_required": False,
            },
            {
                "id": "INT_HIST_01",
                "trigger": "Prior academic warning",
                "title": "Academic Probation Monitoring Agreement",
                "description": "Comprehensive academic contract with bi-weekly milestone milestones signed by student, advisor, and department head.",
                "target_factor": "History",
                "urgency": "High",
                "duration_weeks": 8,
                "oversight_required": True,
            },
        ]

    def recommend_interventions(self, risk_factors: List[str]) -> Dict[str, Any]:
        """Match identified risk factors against the intervention catalog."""
        if not self._catalog:
            self._load_data()

        matched: List[Dict[str, Any]] = []
        matched_ids = set()

        for factor in risk_factors:
            f_lower = factor.lower()
            for item in self._catalog:
                trigger_lower = item["trigger"].lower()
                target_lower = item["target_factor"].lower()

                # Determine if trigger or target factor matches the risk factor string
                matches = (
                    trigger_lower in f_lower
                    or target_lower in f_lower
                    or ("attendance" in f_lower and "attendance" in trigger_lower)
                    or ("performance" in f_lower and "performance" in trigger_lower)
                    or ("failed" in f_lower and "failed" in trigger_lower)
                    or ("assignment" in f_lower and "assignment" in trigger_lower)
                    or ("decline" in f_lower and "performance" in trigger_lower)
                    or ("history" in f_lower and "warning" in trigger_lower)
                )

                if matches and item["id"] not in matched_ids:
                    matched_ids.add(item["id"])
                    matched.append(item)

        # Always return at least the top relevant interventions if matched, or general mentoring
        if not matched:
            matched = [self._catalog[0]]

        # Sort priority: Immediate urgency first, then High, then Medium
        urgency_rank = {"Immediate": 0, "High": 1, "Medium": 2, "Low": 3}
        matched.sort(key=lambda x: urgency_rank.get(x.get("urgency", "Medium"), 9))

        return {
            "status": "success",
            "matched_interventions_count": len(matched),
            "matched_interventions": matched,
            "top_3_recommendations": matched[:3],
        }


def recommend_interventions(risk_factors: List[str]) -> Dict[str, Any]:
    """Convenience function for tool invocation."""
    kb = InterventionKnowledgeBase()
    return kb.recommend_interventions(risk_factors)
