"""LangGraph node execution functions for the AI Academic Early-Warning Engine."""

import time
from datetime import datetime
from typing import Any, Dict
from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent
from agents.planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from memory.long_term_memory import long_term_memory
from workflow.state import AgentState

planning_agent = PlanningAgent()
research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
decision_agent = DecisionAgent()


def planning_node(state: AgentState) -> AgentState:
    """Execute Planning Agent to structure investigation tasks."""
    workflow_id = state.get("workflow_id", f"wf-{int(time.time()*1000)}")
    query = state.get("user_query", "")
    target_ids = state.get("student_ids", [])
    primary_id = target_ids[0] if target_ids else None
    scope = state.get("scope")

    long_term_memory.log_event(workflow_id, "Agent started", "PlanningAgent", f"Decomposing query: '{query}'")

    plan_result = planning_agent.plan(query=query, student_id=primary_id, scope=scope)
    resolved_id = plan_result.get("target_student_id", primary_id or "STU104")

    long_term_memory.log_event(
        workflow_id,
        "Agent completed",
        "PlanningAgent",
        f"Tasks planned: {len(plan_result.get('tasks', []))}"
    )

    metrics = state.get("execution_metrics", {})
    metrics["planning_time_ms"] = round(time.time() * 1000, 2)

    return {
        **state,
        "workflow_id": workflow_id,
        "current_agent": "PlanningAgent",
        "workflow_status": "RUNNING",
        "plan": plan_result,
        "scope": plan_result.get("scope", "individual"),
        "student_ids": [resolved_id],
        "execution_metrics": metrics,
    }


def research_node(state: AgentState) -> AgentState:
    """Execute Research Agent to dispatch tools and collect structured evidence."""
    workflow_id = state.get("workflow_id", "wf-unknown")
    target_id = state.get("student_ids", ["STU104"])[0]
    plan = state.get("plan", {})
    req_tools = plan.get("required_tools")

    long_term_memory.log_event(workflow_id, "Agent started", "ResearchAgent", f"Gathering telemetry for {target_id}")

    start_t = time.time()
    for tool_name in (req_tools or ["attendance_analyzer", "performance_analyzer", "assignment_analyzer", "trend_analyzer"]):
        long_term_memory.log_event(workflow_id, "Tool called", "ResearchAgent", f"Dispatching {tool_name}")

    evidence = research_agent.conduct_research(student_id=target_id, required_tools=req_tools)

    for tool_name in evidence.get("tools_executed", []):
        long_term_memory.log_event(workflow_id, "Tool completed", "ResearchAgent", f"{tool_name} returned data")

    long_term_memory.log_event(
        workflow_id,
        "Agent completed",
        "ResearchAgent",
        f"Aggregated evidence for {target_id}"
    )

    metrics = state.get("execution_metrics", {})
    metrics["research_duration_ms"] = round((time.time() - start_t) * 1000, 2)
    metrics["tools_used_count"] = len(evidence.get("tools_executed", []))

    return {
        **state,
        "current_agent": "ResearchAgent",
        "research_results": evidence,
        "execution_metrics": metrics,
    }


def analysis_node(state: AgentState) -> AgentState:
    """Execute Analysis Agent to perform strictly deterministic risk scoring."""
    workflow_id = state.get("workflow_id", "wf-unknown")
    evidence = state.get("research_results", {})
    target_id = state.get("student_ids", ["STU104"])[0]

    long_term_memory.log_event(workflow_id, "Agent started", "AnalysisAgent", f"Scoring academic risk for {target_id}")

    start_t = time.time()
    analysis_res = analysis_agent.analyze(evidence)

    # Persist risk assessment to Long-Term Memory
    long_term_memory.save_risk_assessment(
        workflow_id=workflow_id,
        student_id=target_id,
        total_risk_score=analysis_res["total_risk_score"],
        risk_band=analysis_res["risk_band"],
        breakdown=analysis_res["breakdown"],
    )

    long_term_memory.log_event(
        workflow_id,
        "Agent completed",
        "AnalysisAgent",
        f"Score: {analysis_res['total_risk_score']}/100 ({analysis_res['risk_band']})"
    )

    metrics = state.get("execution_metrics", {})
    metrics["analysis_duration_ms"] = round((time.time() - start_t) * 1000, 2)

    return {
        **state,
        "current_agent": "AnalysisAgent",
        "analysis": analysis_res,
        "risk_factors": analysis_res.get("risk_factors", []),
        "execution_metrics": metrics,
    }


def decision_node(state: AgentState) -> AgentState:
    """Execute Decision Agent to prescribe pedagogical interventions and review packages."""
    workflow_id = state.get("workflow_id", "wf-unknown")
    analysis_res = state.get("analysis", {})
    target_id = state.get("student_ids", ["STU104"])[0]

    long_term_memory.log_event(workflow_id, "Agent started", "DecisionAgent", f"Formulating remedies for {target_id}")

    start_t = time.time()
    decision_res = decision_agent.formulate_decision(analysis_res)

    # Persist recommended interventions to Long-Term Memory
    long_term_memory.save_interventions(
        workflow_id=workflow_id,
        student_id=target_id,
        interventions=decision_res.get("top_3_interventions", []),
    )

    long_term_memory.log_event(
        workflow_id,
        "Agent completed",
        "DecisionAgent",
        f"Prescribed {len(decision_res.get('top_3_interventions', []))} interventions. Urgency: {decision_res.get('urgency')}"
    )
    long_term_memory.log_event(workflow_id, "Workflow completed", "Orchestrator", f"Workflow {workflow_id} concluded successfully")

    metrics = state.get("execution_metrics", {})
    metrics["decision_duration_ms"] = round((time.time() - start_t) * 1000, 2)
    metrics["completed_at"] = datetime.utcnow().isoformat()

    return {
        **state,
        "current_agent": "DecisionAgent",
        "workflow_status": "COMPLETED",
        "decision": decision_res,
        "execution_metrics": metrics,
    }


def error_node(state: AgentState) -> AgentState:
    """Terminal error node reached after maximum retries or unrecoverable failures."""
    workflow_id = state.get("workflow_id", "wf-unknown")
    err_msg = "Workflow terminated: maximum retry limit (3) exceeded or unrecoverable error encountered."

    errors = state.get("errors", [])
    errors.append(err_msg)

    long_term_memory.log_event(workflow_id, "Workflow failed", "ErrorNode", err_msg)

    return {
        **state,
        "current_agent": "ErrorNode",
        "workflow_status": "FAILED",
        "errors": errors,
    }
