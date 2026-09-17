"""Unit tests for LangGraph multi-agent workflow, validators, router, executor, and batch analysis."""

import pytest
from workflow.batch_analysis import batch_analyzer
from workflow.executor import workflow_executor
from workflow.graph import run_academic_workflow
from workflow.router import (
    MAX_RETRIES,
    route_after_analysis,
    route_after_decision,
    route_after_research,
)
from workflow.validators import (
    validate_analysis_state,
    validate_decision_state,
    validate_research_state,
)


def test_state_validators():
    """Verify validation gates correctly enforce required fields."""
    # Valid research state
    valid_res_state = {
        "research_results": {
            "status": "success",
            "attendance": {"status": "success"},
            "performance": {"status": "success"},
        }
    }
    assert validate_research_state(valid_res_state) is True

    # Invalid research state
    assert validate_research_state({"research_results": {}}) is False

    # Valid analysis state
    valid_analysis_state = {
        "analysis": {
            "status": "success",
            "total_risk_score": 89,
            "risk_band": "CRITICAL",
        }
    }
    assert validate_analysis_state(valid_analysis_state) is True

    # Invalid analysis state (out of bounds)
    assert validate_analysis_state({"analysis": {"status": "success", "total_risk_score": 150}}) is False

    # Valid decision state
    valid_decision_state = {
        "decision": {
            "status": "success",
            "top_3_interventions": [{"title": "Plan A"}],
            "human_review_package": {"status": "ready"},
        }
    }
    assert validate_decision_state(valid_decision_state) is True


def test_router_retry_bounds_and_error_node():
    """Verify conditional router enforces MAX_RETRIES (3) and avoids infinite loops."""
    # Incomplete research with retry_count = 0 -> retry "research"
    incomplete_state = {"research_results": {}, "retry_count": 0}
    assert route_after_research(incomplete_state) == "research"

    # Incomplete research with retry_count = 3 -> terminal "error_node"
    exceeded_state = {"research_results": {}, "retry_count": 3}
    assert route_after_research(exceeded_state) == "error_node"

    # Valid research -> "analysis"
    valid_state = {
        "research_results": {
            "status": "success",
            "attendance": {"status": "success"},
            "performance": {"status": "success"},
        },
        "retry_count": 0,
    }
    assert route_after_research(valid_state) == "analysis"


def test_full_workflow_execution_stu104():
    """Verify end-to-end LangGraph execution on demonstration student STU104."""
    state = run_academic_workflow("Analyze student STU104", student_id="STU104")
    
    assert state["workflow_status"] == "COMPLETED"
    assert state["current_agent"] == "DecisionAgent"
    assert state["workflow_id"].startswith("wf-")
    assert state["analysis"]["total_risk_score"] == 89
    assert state["analysis"]["risk_band"] == "CRITICAL"
    assert len(state["decision"]["top_3_interventions"]) == 3
    assert state["execution_metrics"]["total_duration_ms"] > 0


def test_workflow_executor_tracking():
    """Verify WorkflowExecutor tracks status, duration, and tools used."""
    record = workflow_executor.execute_sync("Analyze STU104", student_id="STU104")
    assert record["status"] == "COMPLETED"
    assert record["workflow_id"].startswith("wf-")
    assert len(record["tools_used"]) >= 4
    assert record["duration_ms"] > 0

    # Test registry lookup
    retrieved = workflow_executor.get_status(record["workflow_id"])
    assert retrieved is not None
    assert retrieved["workflow_id"] == record["workflow_id"]


def test_cohort_batch_analysis_distribution():
    """Verify batch cohort triage produces exact verified risk distribution."""
    cohort_result = batch_analyzer.analyze_cohort("CSE-A")
    
    assert cohort_result["status"] == "success"
    assert cohort_result["total_students"] == 60
    
    dist = cohort_result["distribution"]
    assert dist["Critical"] == 2
    assert dist["High"] == 3
    assert dist["Medium"] == 10
    assert dist["Low"] == 45
    
    assert "STU104" in cohort_result["critical_student_ids"]
    assert "STU112" in cohort_result["critical_student_ids"]
