"""Validation gates for multi-agent workflow state transitions."""

import logging
from typing import Any, Dict
from workflow.state import AgentState

logger = logging.getLogger("academic_risk.validators")


def validate_research_state(state: AgentState) -> bool:
    """Verify that research evidence was successfully collected."""
    results = state.get("research_results", {})
    if not results or results.get("status") == "not_found":
        logger.warning("Research validation failed: empty or not_found results.")
        return False

    # Check for attendance and performance presence
    has_attendance = "attendance" in results and results["attendance"].get("status") == "success"
    has_performance = "performance" in results and results["performance"].get("status") == "success"

    if not (has_attendance or has_performance):
        logger.warning("Research validation failed: missing essential telemetry.")
        return False

    return True


def validate_analysis_state(state: AgentState) -> bool:
    """Verify that deterministic risk score and breakdown were accurately computed."""
    analysis = state.get("analysis", {})
    if not analysis or analysis.get("status") != "success":
        logger.warning("Analysis validation failed: incomplete or non-success analysis.")
        return False

    total = analysis.get("total_risk_score")
    band = analysis.get("risk_band")

    if total is None or not isinstance(total, (int, float)) or not (0 <= total <= 100):
        logger.warning("Analysis validation failed: invalid total_risk_score %s.", total)
        return False

    if band not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        logger.warning("Analysis validation failed: invalid risk_band %s.", band)
        return False

    return True


def validate_decision_state(state: AgentState) -> bool:
    """Verify that actionable interventions and human review packages are formed."""
    decision = state.get("decision", {})
    if not decision or decision.get("status") != "success":
        logger.warning("Decision validation failed: missing decision package.")
        return False

    top_interventions = decision.get("top_3_interventions", [])
    if not top_interventions:
        logger.warning("Decision validation failed: no interventions prescribed.")
        return False

    if not decision.get("human_review_package"):
        logger.warning("Decision validation failed: missing human_review_package.")
        return False

    return True
