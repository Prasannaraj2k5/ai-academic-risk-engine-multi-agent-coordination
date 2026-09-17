"""LangGraph Multi-Agent Workflow Construction and Execution.

Flow:
START
  ↓
Planning
  ↓
Research
  ↓
Research Validation (conditional)
  ↓
Analysis
  ↓
Analysis Validation (conditional)
  ↓
Decision
  ↓
Final Validation (conditional)
  ↓
END
"""

import time
import uuid
from typing import Any, Dict, Optional
from langgraph.graph import END, START, StateGraph

from memory.long_term_memory import long_term_memory
from memory.short_term_memory import short_term_memory
from workflow.nodes import (
    analysis_node,
    decision_node,
    error_node,
    planning_node,
    research_node,
)
from workflow.router import (
    route_after_analysis,
    route_after_decision,
    route_after_research,
)
from workflow.state import AgentState


def build_academic_graph():
    """Build and compile the LangGraph StateGraph."""
    builder = StateGraph(AgentState)

    # 1. Add operational nodes
    builder.add_node("planning", planning_node)
    builder.add_node("research", research_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("decision", decision_node)
    builder.add_node("error_node", error_node)

    # 2. Add edges and conditional transitions
    builder.add_edge(START, "planning")
    builder.add_edge("planning", "research")

    builder.add_conditional_edges(
        "research",
        route_after_research,
        {
            "analysis": "analysis",
            "research": "research",
            "error_node": "error_node",
        },
    )

    builder.add_conditional_edges(
        "analysis",
        route_after_analysis,
        {
            "decision": "decision",
            "research": "research",
            "analysis": "analysis",
            "error_node": "error_node",
        },
    )

    builder.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "__end__": END,
            "decision": "decision",
            "error_node": "error_node",
        },
    )

    builder.add_edge("error_node", END)

    return builder.compile()


# Compiled singleton graph
academic_graph = build_academic_graph()


def run_academic_workflow(
    query: str,
    student_id: Optional[str] = None,
    session_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    scope: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the compiled multi-agent LangGraph workflow."""
    sess_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
    wf_id = workflow_id or f"wf-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"

    # Resolve student context from short term memory if needed
    resolved_student = student_id or short_term_memory.resolve_student_id(sess_id, query) or "STU104"

    long_term_memory.log_event(
        workflow_id=wf_id,
        event_type="Workflow started",
        agent_name="Orchestrator",
        details=f"Query: '{query}', Target: {resolved_student}, Scope: {scope or 'individual'}",
    )

    initial_state: AgentState = {
        "user_query": query,
        "session_id": sess_id,
        "student_ids": [resolved_student],
        "scope": scope or "individual",
        "plan": {},
        "research_results": {},
        "risk_factors": [],
        "analysis": {},
        "decision": {},
        "errors": [],
        "workflow_status": "QUEUED",
        "current_agent": "START",
        "retry_count": 0,
        "execution_metrics": {
            "started_at": time.time(),
            "workflow_id": wf_id,
        },
        "conversation_context": short_term_memory.get_session_context(sess_id),
        "workflow_id": wf_id,
    }

    start_perf = time.time()
    final_state = academic_graph.invoke(initial_state)
    total_duration_ms = round((time.time() - start_perf) * 1000, 2)

    # Update execution metrics
    metrics = final_state.get("execution_metrics", {})
    metrics["total_duration_ms"] = total_duration_ms
    final_state["execution_metrics"] = metrics

    # Record turn in short term memory
    analysis_res = final_state.get("analysis", {})
    summary_text = (
        f"Student {resolved_student} assessed at {analysis_res.get('risk_band')} Risk "
        f"(Score: {analysis_res.get('total_risk_score')}/100)."
    )
    short_term_memory.record_turn(
        session_id=sess_id,
        query=query,
        response=summary_text,
        student_id=resolved_student,
        context={"workflow_id": wf_id, "score": analysis_res.get("total_risk_score")},
    )

    return final_state
