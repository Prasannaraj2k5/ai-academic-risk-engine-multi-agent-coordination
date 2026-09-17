"""Planning Agent.

Responsibilities:
- Understand user request and intent
- Identify whether individual or cohort analysis is needed
- Decompose request into structured investigation tasks
- Select appropriate tools from the 6 academic tools
- Must NOT calculate final risk score
"""

import re
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent


class PlanningAgent(BaseAgent):
    """Specialized agent that orchestrates analytical investigation plans."""

    def __init__(self):
        super().__init__(agent_name="PlanningAgent", temperature=0.1)

    def plan(
        self,
        query: str,
        student_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Decompose request into a concrete investigation plan without computing risk scores."""
        clean_q = query.strip() if query else ""
        resolved_scope = scope or ("cohort" if any(w in clean_q.lower() for w in ["cohort", "class", "all students", "cse-a"]) else "individual")

        # Extract or resolve student ID
        resolved_student_id = student_id
        if not resolved_student_id:
            match = re.search(r"\b(STU\d{3})\b", clean_q, re.IGNORECASE)
            if match:
                resolved_student_id = match.group(1).upper()
            elif resolved_scope == "individual":
                resolved_student_id = "STU104"  # Default canonical student

        # Standard tool suite required for comprehensive academic investigation
        required_tools = [
            "student_profile",
            "attendance_analyzer",
            "performance_analyzer",
            "assignment_analyzer",
            "trend_analyzer",
            "intervention_knowledge",
        ]

        investigation_tasks = [
            {
                "task_id": "TASK_01",
                "tool": "student_profile",
                "description": f"Extract demographic profile and course enrollment for {resolved_student_id or 'cohort'}",
            },
            {
                "task_id": "TASK_02",
                "tool": "attendance_analyzer",
                "description": "Assess overall attendance and identify any subjects below critical (<66%) and warning (66-74.99%) thresholds",
            },
            {
                "task_id": "TASK_03",
                "tool": "performance_analyzer",
                "description": "Evaluate subject-wise marks, compute current average, and identify failed assessments (<50%)",
            },
            {
                "task_id": "TASK_04",
                "tool": "assignment_analyzer",
                "description": "Inspect coursework submissions, missed deliverables, and submission delays",
            },
            {
                "task_id": "TASK_05",
                "tool": "trend_analyzer",
                "description": "Calculate semester-over-semester delta and flag significant academic declines (>15% drop)",
            },
            {
                "task_id": "TASK_06",
                "tool": "intervention_knowledge",
                "description": "Cross-reference identified risk triggers with institutional intervention playbook",
            },
        ]

        plan_summary = (
            f"Plan generated for {resolved_scope.upper()} analysis "
            f"(Target: {resolved_student_id or 'Cohort CSE-A'}). "
            f"6 specialized tools scheduled across telemetry ingestion, trend analysis, and intervention mapping."
        )

        return {
            "agent": self.agent_name,
            "status": "planned",
            "scope": resolved_scope,
            "target_student_id": resolved_student_id,
            "required_tools": required_tools,
            "tasks": investigation_tasks,
            "summary": plan_summary,
            "is_live_llm": self.is_live_llm,
        }
