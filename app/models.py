from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Severity = Literal["HIGH", "MEDIUM", "LOW"]

class Evidence(BaseModel):
    doc: str                                 # filename
    page: Optional[int] = None               # 1-based
    bbox: Optional[List[float]] = None       # [x1,y1,x2,y2] if available
    text_snippet: Optional[str] = None
    hash: Optional[str] = None               # content hash/version

class ClauseFrame(BaseModel):
    """
    Schema-agnostic clause representation.
    Works for fees, deadlines, prohibitions, notices, covenants, etc.
    """
    id: str
    subject: str                             # e.g., "Institution A" / "Borrower" / "All Investors"
    obligation: str                          # e.g., "pay", "report", "prohibit", "maintain", "notify"
    attribute: Optional[str] = None          # e.g., "management_fee", "sector", "ltv_ratio"
    comparator: Optional[str] = None         # e.g., "eq","lte","gte","in","not_in","contains","absent"
    value: Optional[Any] = None              # number/string/list/dict
    unit: Optional[str] = None               # "%","days","bps","USD","SIC","NAICS", etc.
    conditions: Optional[List[str]] = None   # e.g., ["quarter_end", "except_index_funds"]
    effective_start: Optional[str] = None    # ISO date
    effective_end: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence: Evidence
    raw: Optional[Dict[str, Any]] = None     # full ADE item or intermediate JSON

class ExtractResult(BaseModel):
    doc: str
    doc_hash: Optional[str] = None
    frames: List[ClauseFrame]

class PolicyRule(BaseModel):
    """
    A generic, executable rule derived from a ClauseFrame.
    """
    id: str
    selector: Dict[str, Any]                 # who/what it applies to (e.g., {"subject.eq":"Institution A"})
    check: Dict[str, Any]                    # normalized assertion (see Rule DSL below)
    on_events: List[str]                     # e.g., ["fee_post","report_delivered","trade_allocated"]
    severity: Severity = "HIGH"
    evidence: Evidence
    comments: Optional[str] = None           # human-readable explanation

class FactEvent(BaseModel):
    """
    Arbitrary real-time fact coming from Pathway streams.
    """
    type: str                                # "fee_post","report_delivered","trade_allocated", etc.
    payload: Dict[str, Any]                  # e.g., {"subject":"Institution A","fee_rate":0.0200}

class Violation(BaseModel):
    id: str
    rule_id: str
    event_type: str
    subject: str
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    severity: Severity
    evidence: Evidence
    detected_at: str                         # ISO-8601
