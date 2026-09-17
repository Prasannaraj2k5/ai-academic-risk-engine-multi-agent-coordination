"""Research Agent.

Responsibilities:
- Execute investigation plan dispatched by Planning Agent
- Dispatch the 6 specialized academic tools
- Aggregate structured telemetry and qualitative records
- Return comprehensive evidence bundle to shared state
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from tools.assignment_analyzer import analyze_assignments
from tools.attendance_analyzer import analyze_attendance
from tools.intervention_knowledge import recommend_interventions
from tools.performance_analyzer import analyze_performance
from tools.student_profile import get_student_profile
from tools.trend_analyzer import analyze_trend


class ResearchAgent(BaseAgent):
    """Specialized agent that executes tool queries and aggregates evidence."""

    def __init__(self):
        super().__init__(agent_name="ResearchAgent", temperature=0.1)

    def conduct_research(
        self,
        student_id: str,
        required_tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Dispatch academic tools for student_id and return structured evidence dictionary."""
        tools_to_run = required_tools or [
            "student_profile",
            "attendance_analyzer",
            "performance_analyzer",
            "assignment_analyzer",
            "trend_analyzer",
        ]

        evidence: Dict[str, Any] = {
            "student_id": student_id,
            "status": "success",
            "tools_executed": [],
        }

        # 1. Student Profile
        if "student_profile" in tools_to_run:
            prof = get_student_profile(student_id)
            evidence["profile"] = prof
            evidence["tools_executed"].append("student_profile")

        # 2. Attendance
        if "attendance_analyzer" in tools_to_run:
            att = analyze_attendance(student_id)
            evidence["attendance"] = att
            evidence["tools_executed"].append("attendance_analyzer")

        # 3. Performance
        if "performance_analyzer" in tools_to_run:
            perf = analyze_performance(student_id)
            evidence["performance"] = perf
            evidence["tools_executed"].append("performance_analyzer")

        # 4. Assignments
        if "assignment_analyzer" in tools_to_run:
            asn = analyze_assignments(student_id)
            evidence["assignments"] = asn
            evidence["tools_executed"].append("assignment_analyzer")

        # 5. Trend
        if "trend_analyzer" in tools_to_run:
            tr = analyze_trend(student_id)
            evidence["trend"] = tr
            evidence["tools_executed"].append("trend_analyzer")

        # Summarize key evidence findings
        att_data = evidence.get("attendance", {})
        perf_data = evidence.get("performance", {})
        tr_data = evidence.get("trend", {})
        asn_data = evidence.get("assignments", {})

        summary = (
            f"Evidence aggregated for {student_id}: Attendance={att_data.get('overall_attendance_pct')}%, "
            f"Current Avg={perf_data.get('current_average_pct')}%, Prior Avg={tr_data.get('previous_semester_avg')}%, "
            f"Failed Assessments={perf_data.get('failed_assessments_count')}, "
            f"Missed Assignments={asn_data.get('missed_count')}, Late Assignments={asn_data.get('late_count')}."
        )
        evidence["summary"] = summary
        evidence["agent"] = self.agent_name

        return evidence
