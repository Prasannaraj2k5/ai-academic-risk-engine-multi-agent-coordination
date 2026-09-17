"""Conditional routing logic and retry threshold guards for LangGraph workflow."""

import logging
from typing import Literal
from workflow.state import AgentState
from workflow.validators import (
    validate_analysis_state,
    validate_decision_state,
    validate_research_state,
)

logger = logging.getLogger("academic_risk.router")
MAX_RETRIES = 3


def route_after_research(state: AgentState) -> Literal["analysis", "research", "error_node"]:
    """Route to analysis if research evidence valid; retry or error otherwise."""
    retry_count = state.get("retry_count", 0)

    if validate_research_state(state):
        return "analysis"

    if retry_count < MAX_RETRIES:
        logger.info("Research incomplete. Retrying research node (attempt %d/%d).", retry_count + 1, MAX_RETRIES)
        return "research"

    logger.error("Research failed after exceeding maximum retries (%d). Routing to error_node.", MAX_RETRIES)
    return "error_node"


def route_after_analysis(state: AgentState) -> Literal["decision", "research", "analysis", "error_node"]:
    """Route to decision if analysis valid; back to research if evidence missing; retry or error."""
    retry_count = state.get("retry_count", 0)
    research_results = state.get("research_results", {})

    # Check if analysis failed due to missing evidence
    if not research_results or not validate_research_state(state):
        if retry_count < MAX_RETRIES:
            logger.info("Analysis lacks evidence. Routing back to research node.")
            return "research"
        return "error_node"

    if validate_analysis_state(state):
        return "decision"

    if retry_count < MAX_RETRIES:
        logger.info("Analysis invalid. Retrying analysis node (attempt %d/%d).", retry_count + 1, MAX_RETRIES)
        return "analysis"

    logger.error("Analysis failed after exceeding maximum retries (%d). Routing to error_node.", MAX_RETRIES)
    return "error_node"


def route_after_decision(state: AgentState) -> Literal["__end__", "decision", "error_node"]:
    """Route to END if decision valid; retry or error otherwise."""
    retry_count = state.get("retry_count", 0)

    if validate_decision_state(state):
        return "__end__"

    if retry_count < MAX_RETRIES:
        logger.info("Decision invalid. Retrying decision node (attempt %d/%d).", retry_count + 1, MAX_RETRIES)
        return "decision"

    logger.error("Decision failed after exceeding maximum retries (%d). Routing to error_node.", MAX_RETRIES)
    return "error_node"
