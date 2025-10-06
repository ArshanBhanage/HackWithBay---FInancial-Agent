import os
from typing import Optional
from pdfminer.high_level import extract_text
from app.agents.roles import PlannerAgent, PlannerDecision
from app.tools.anthropic_client import ask_json

SYSTEM = """You are a planning agent for contract analysis.
Output ONLY valid JSON with keys: mode, targets, confidence_threshold.
- mode ∈ {"ade_only","hybrid","fallback"}
- targets: array of coarse targets such as ["fees","deadlines","prohibitions","collateral","notices","covenants","ratios","eligibility","termination","governance"]
- confidence_threshold: float 0..1 for extraction acceptance.
Choose ade_only if the document looks like a contract/policy with structured clauses.
Choose hybrid if OCR/table/scan issues may require LLM normalization.
Choose fallback only if the document is clearly non-contractual or unreadable.
"""

PROMPT_TMPL = """Document name: {name}
First 1200 chars (for context):
---
{hint}
---
Return your JSON plan."""

class Planner(PlannerAgent):
    def run(self, doc_path: str, doc_text_hint: Optional[str]=None) -> PlannerDecision:
        try:
            hint = doc_text_hint or extract_text(doc_path)[:1200]
        except Exception:
            hint = "(could not extract text)"
        payload = ask_json(SYSTEM, PROMPT_TMPL.format(name=os.path.basename(doc_path), hint=hint))
        return PlannerDecision(**payload)
