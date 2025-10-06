from __future__ import annotations
from typing import Dict, Any
from app.agents.roles import ExplainerAgent
from app.tools.anthropic_client import ask_json

SYS = """You are a concise explainer. Output JSON {"summary": "..."} only.
Explain a contract violation in one or two short sentences, non-judgmental, include the expected vs actual and reference the evidence doc+page when available.
"""

class Explainer(ExplainerAgent):
    def run(self, violation: Dict[str, Any]) -> str:
        v = violation
        user = (
            "Violation:\n"
            f"- Rule ID: {v.get('rule_id')}\n"
            f"- Subject: {v.get('subject')}\n"
            f"- Event: {v.get('event_type')}\n"
            f"- Expected: {v.get('expected')}\n"
            f"- Actual: {v.get('actual')}\n"
            f"- Evidence: {v.get('evidence')}\n"
        )
        out = ask_json(SYS, user)
        return out.get("summary","")
