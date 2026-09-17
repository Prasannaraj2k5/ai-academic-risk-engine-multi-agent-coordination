"""Workflow Execution Tracking and Registry.

Tracks:
- workflow_id
- status: QUEUED, RUNNING, COMPLETED, FAILED
- current agent
- start time, end time, duration
- retry count
- tools used
- errors
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from workflow.graph import run_academic_workflow


class WorkflowExecutionRecord:
    """In-memory state tracker for a single workflow lifecycle."""

    def __init__(self, workflow_id: str, query: str, student_id: Optional[str] = None):
        self.workflow_id = workflow_id
        self.query = query
        self.student_id = student_id
        self.status = "QUEUED"  # QUEUED, RUNNING, COMPLETED, FAILED
        self.current_agent = "START"
        self.start_time = datetime.utcnow().isoformat()
        self.end_time: Optional[str] = None
        self.duration_ms: float = 0.0
        self.retry_count: int = 0
        self.tools_used: List[str] = []
        self.errors: List[str] = []
        self.result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to serializable dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "query": self.query,
            "student_id": self.student_id,
            "status": self.status,
            "current_agent": self.current_agent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "tools_used": self.tools_used,
            "errors": self.errors,
            "result": self.result,
        }


class WorkflowExecutor:
    """Registry and execution supervisor for academic analysis workflows."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(WorkflowExecutor, cls).__new__(cls)
                    cls._instance._registry: Dict[str, WorkflowExecutionRecord] = {}
        return cls._instance

    def execute_sync(
        self,
        query: str,
        student_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute workflow synchronously and register telemetry."""
        wf_id = f"wf-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"
        record = WorkflowExecutionRecord(wf_id, query, student_id)
        self._registry[wf_id] = record

        record.status = "RUNNING"
        record.current_agent = "PlanningAgent"
        start_t = time.time()

        try:
            final_state = run_academic_workflow(
                query=query,
                student_id=student_id,
                session_id=session_id,
                workflow_id=wf_id,
                scope=scope,
            )
            record.duration_ms = round((time.time() - start_t) * 1000, 2)
            record.end_time = datetime.utcnow().isoformat()
            record.status = final_state.get("workflow_status", "COMPLETED")
            record.current_agent = final_state.get("current_agent", "DecisionAgent")
            record.retry_count = final_state.get("retry_count", 0)
            record.errors = final_state.get("errors", [])

            # Extract tools used
            res_results = final_state.get("research_results", {})
            record.tools_used = res_results.get("tools_executed", [])

            record.result = {
                "workflow_id": wf_id,
                "analysis": final_state.get("analysis", {}),
                "decision": final_state.get("decision", {}),
                "risk_factors": final_state.get("risk_factors", []),
                "research_summary": res_results.get("summary", ""),
            }
            return record.to_dict()

        except Exception as e:
            record.status = "FAILED"
            record.duration_ms = round((time.time() - start_t) * 1000, 2)
            record.end_time = datetime.utcnow().isoformat()
            record.errors.append(str(e))
            return record.to_dict()

    def get_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve telemetry status for a workflow."""
        record = self._registry.get(workflow_id)
        return record.to_dict() if record else None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """List all executed workflows."""
        return [r.to_dict() for r in self._registry.values()]


# Singleton executor
workflow_executor = WorkflowExecutor()
