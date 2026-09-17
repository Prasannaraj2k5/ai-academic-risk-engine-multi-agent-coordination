"""Unit tests for specialized academic agents."""

import pytest
from agents.base_agent import BaseAgent
from agents.planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent


def test_base_agent_initialization():
    """Verify BaseAgent initializes safely without crashing when API key is unset."""
    agent = BaseAgent(agent_name="TestAgent")
    assert agent.agent_name == "TestAgent"
    assert isinstance(agent.is_live_llm, bool)

    # Test fallback query response
    res = agent.ask("What is academic risk?")
    assert res["status"] == "success"
    assert "academic risk" in res["question"].lower()
    assert len(res["response"]) > 20
    assert "gsk_" not in res["response"]  # No secret leakage


def test_planning_agent_individual_and_cohort():
    """Verify PlanningAgent generates investigation tasks without computing risk scores."""
    planner = PlanningAgent()
    
    # Individual plan
    plan_ind = planner.plan(query="Analyze STU104", student_id="STU104")
    assert plan_ind["status"] == "planned"
    assert plan_ind["scope"] == "individual"
    assert plan_ind["target_student_id"] == "STU104"
    assert len(plan_ind["tasks"]) >= 5
    assert "total_risk_score" not in plan_ind  # Planning agent must not score!

    # Cohort plan
    plan_cohort = planner.plan(query="Analyze all students in CSE-A cohort")
    assert plan_cohort["scope"] == "cohort"


def test_research_agent_evidence_collection():
    """Verify ResearchAgent dispatches tools and gathers structured telemetry."""
    researcher = ResearchAgent()
    evidence = researcher.conduct_research(student_id="STU104")
    
    assert evidence["status"] == "success"
    assert evidence["student_id"] == "STU104"
    assert "attendance" in evidence
    assert "performance" in evidence
    assert "assignments" in evidence
    assert "trend" in evidence
    assert evidence["attendance"]["overall_attendance_pct"] == 68.0


def test_analysis_agent_deterministic_scoring_stu104():
    """Verify AnalysisAgent calculates exact 89/100 for demonstration student STU104."""
    researcher = ResearchAgent()
    evidence = researcher.conduct_research(student_id="STU104")

    analyzer = AnalysisAgent()
    analysis = analyzer.analyze(evidence)

    assert analysis["status"] == "success"
    assert analysis["total_risk_score"] == 89
    assert analysis["risk_band"] == "CRITICAL"
    
    breakdown = analysis["breakdown"]
    assert breakdown["performance"] == 30
    assert breakdown["attendance"] == 25
    assert breakdown["assignments"] == 17
    assert breakdown["assessments"] == 10
    assert breakdown["history"] == 7
    assert sum(breakdown.values()) == 89


def test_decision_agent_interventions_and_review():
    """Verify DecisionAgent creates top 3 interventions and human-review package."""
    researcher = ResearchAgent()
    evidence = researcher.conduct_research(student_id="STU104")
    analyzer = AnalysisAgent()
    analysis = analyzer.analyze(evidence)

    decision_maker = DecisionAgent()
    decision = decision_maker.formulate_decision(analysis)

    assert decision["status"] == "success"
    assert decision["urgency"] == "Immediate"
    assert decision["faculty_oversight"] == "Required"
    assert decision["follow_up_period"] == "Within 7 Days"
    assert len(decision["top_3_interventions"]) == 3
    
    review_pkg = decision["human_review_package"]
    assert review_pkg["eligible_actions"] == ["APPROVE", "MODIFY", "REJECT"]
