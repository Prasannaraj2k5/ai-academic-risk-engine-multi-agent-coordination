"""Shared AgentState schema for LangGraph multi-agent workflow."""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across LangGraph nodes."""

    user_query: str
    session_id: str
    student_ids: List[str]
    scope: str  # "individual" or "cohort"
    plan: Dict[str, Any]
    research_results: Dict[str, Any]
    risk_factors: List[str]
    analysis: Dict[str, Any]
    decision: Dict[str, Any]
    errors: List[str]
    workflow_status: str  # "QUEUED", "RUNNING", "COMPLETED", "FAILED"
    current_agent: str
    retry_count: int
    execution_metrics: Dict[str, Any]
    conversation_context: Dict[str, Any]
    workflow_id: str
