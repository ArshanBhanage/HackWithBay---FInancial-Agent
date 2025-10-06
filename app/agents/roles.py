from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel
from app.models import ExtractResult, ClauseFrame, PolicyRule

class PlannerDecision(BaseModel):
    mode: str                 # "ade_only" | "hybrid" | "fallback"
    targets: List[str]        # extraction targets or hints (e.g., ["fees","deadlines","prohibitions"])
    confidence_threshold: float = 0.6

class PlannerAgent:
    """LLM (Claude) decides extraction strategy and target hints per document."""
    def run(self, doc_path: str, doc_text_hint: str|None=None) -> PlannerDecision:
        raise NotImplementedError

class ExtractorAgent:
    """Uses LandingAI ADE; can enrich/normalize frames with LLM if needed."""
    def run(self, doc_path: str, decision: PlannerDecision) -> ExtractResult:
        raise NotImplementedError

class CompilerAgent:
    """Maps ClauseFrames -> PolicyRules using the generic DSL."""
    def run(self, frames: List[ClauseFrame]) -> List[PolicyRule]:
        raise NotImplementedError

class ValidatorAgent:
    """Evaluates incoming facts (Pathway stream) against rules."""
    def run(self, rule_index: Any, fact_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

class ExplainerAgent:
    """Turns violations into human-friendly summaries for UI/Slack."""
    def run(self, violation: Dict[str, Any]) -> str:
        raise NotImplementedError
