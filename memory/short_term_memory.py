"""Short-Term Memory System for multi-turn conversational context retention.

Maintains:
- Session ID mapping
- Active target student context (e.g., STU104)
- Previous user queries and responses
- Conversational entity resolution ("Analyze STU104" followed by "What about attendance?")
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class ShortTermMemory:
    """In-memory session registry maintaining dialogue history and active student focus."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShortTermMemory, cls).__new__(cls)
            cls._instance._sessions: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Fetch or initialize a session structure."""
        if not session_id:
            session_id = "default-session"
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "current_student_id": None,
                "history": [],
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "metadata": {},
            }
        return self._sessions[session_id]

    def record_turn(
        self,
        session_id: str,
        query: str,
        response: str,
        student_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store an interaction turn in the session ledger."""
        session = self.get_or_create_session(session_id)
        if student_id:
            session["current_student_id"] = student_id

        turn_entry = {
            "query": query,
            "response": response,
            "student_id": student_id or session.get("current_student_id"),
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        session["history"].append(turn_entry)
        session["last_active"] = datetime.utcnow().isoformat()

    def resolve_student_id(self, session_id: str, query: str) -> Optional[str]:
        """Extract student ID from query, or fall back to the active session student."""
        # 1. Look for explicit pattern like STU101 - STU160 in query
        match = re.search(r"\b(STU\d{3})\b", query, re.IGNORECASE)
        if match:
            found_id = match.group(1).upper()
            session = self.get_or_create_session(session_id)
            session["current_student_id"] = found_id
            return found_id

        # 2. Check if query asks a follow-up ("attendance", "performance", "risk", "interventions")
        # and there is an active student in this session
        session = self.get_or_create_session(session_id)
        current = session.get("current_student_id")
        if current:
            return current

        return None

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieve full context dictionary for state injection."""
        session = self.get_or_create_session(session_id)
        return {
            "session_id": session_id,
            "active_student": session.get("current_student_id"),
            "turns_count": len(session.get("history", [])),
            "recent_turns": session.get("history", [])[-3:],
        }

    def clear_session(self, session_id: str) -> None:
        """Reset a specific session."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton helper
short_term_memory = ShortTermMemory()
