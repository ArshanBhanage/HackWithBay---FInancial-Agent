"""Obligation ontology models for financial contract analysis."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ObligationType(str, Enum):
    """Types of financial obligations."""
    FEE_RATE = "fee.rate_percent"
    FEE_AMOUNT = "fee.amount"
    REPORTING_DEADLINE = "reporting.deadline_days"
    ALLOCATION_RESTRICTION = "allocation.prohibited_sector"
    MFN_NOTICE = "mfn.notice_required"
    COVENANT = "covenant.requirement"
    COLLATERAL = "collateral.requirement"
    INTEREST_RATE = "interest.rate_percent"
    MATURITY_DATE = "maturity.date"
    EARLY_REPAYMENT = "repayment.early_restriction"


class SeverityLevel(str, Enum):
    """Severity levels for obligations and alerts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EnforcementAction(str, Enum):
    """Actions to take when obligations are violated."""
    ALERT = "alert"
    BLOCK = "block"
    CREATE_TASK = "create_task"
    LOG_ONLY = "log_only"


class Beneficiary(BaseModel):
    """Entity that benefits from or is subject to an obligation."""
    id: str
    legal_name: str
    type: str  # "investor", "lender", "insurer", etc.
    metadata: Optional[Dict[str, Any]] = None


class Trigger(BaseModel):
    """Event that triggers an obligation check."""
    event_type: str  # "quarter_end", "fee_calculation", "trade_allocation", etc.
    conditions: Optional[Dict[str, Any]] = None


class Action(BaseModel):
    """Action required when an obligation is triggered."""
    action_type: str
    parameters: Optional[Dict[str, Any]] = None


class Exception(BaseModel):
    """Exception to an obligation rule."""
    condition: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class EffectivePeriod(BaseModel):
    """Time period when an obligation is effective."""
    start: datetime
    end: Optional[datetime] = None


class Evidence(BaseModel):
    """Evidence linking an obligation to source document."""
    document_name: str
    page_number: int
    text_snippet: str
    table_cell: Optional[str] = None
    confidence_score: Optional[float] = None


class Obligation(BaseModel):
    """Core obligation model representing a financial contract requirement."""
    id: str
    type: ObligationType
    applies_to: Union[str, List[str]]  # Beneficiary ID(s) or "ALL_INVESTORS"
    expected_value: Any
    basis: Optional[str] = None  # e.g., "management_fee", "interest_rate"
    
    # Temporal validity
    effective_period: EffectivePeriod
    
    # Evidence and traceability
    evidence: Evidence
    
    # Risk and enforcement
    severity: SeverityLevel
    enforcement: Dict[str, Any]  # Contains "when" and "action" keys
    
    # Optional fields
    exceptions: Optional[List[Exception]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Computed fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def is_applicable_to(self, beneficiary_id: str) -> bool:
        """Check if this obligation applies to a specific beneficiary."""
        if isinstance(self.applies_to, str):
            return self.applies_to == beneficiary_id or self.applies_to == "ALL_INVESTORS"
        return beneficiary_id in self.applies_to
    
    def is_effective_at(self, timestamp: datetime) -> bool:
        """Check if this obligation is effective at a given timestamp."""
        if self.effective_period.start > timestamp:
            return False
        if self.effective_period.end and self.effective_period.end < timestamp:
            return False
        return True
    
    def get_risk_score(self) -> int:
        """Calculate risk score based on severity and type."""
        severity_scores = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4
        }
        return severity_scores.get(self.severity, 0)
