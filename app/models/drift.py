"""Drift detection models for contract changes."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    """Types of changes detected in contracts."""
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_MODIFIED = "field_modified"
    CLAUSE_ADDED = "clause_added"
    CLAUSE_REMOVED = "clause_removed"
    CLAUSE_MODIFIED = "clause_modified"
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    TABLE_MODIFIED = "table_modified"
    STRUCTURAL_CHANGE = "structural_change"


class DriftChange(BaseModel):
    """A specific change detected between contract versions."""
    change_id: str
    change_type: ChangeType
    field_name: Optional[str] = None
    
    # Values
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Context
    page_number: Optional[int] = None
    text_snippet: Optional[str] = None
    table_cell: Optional[str] = None
    
    # Impact assessment
    risk_impact: str = "unknown"  # low, medium, high, critical
    financial_impact: Optional[float] = None
    legal_impact: Optional[str] = None
    
    # Evidence
    evidence: Dict[str, Any] = {}
    confidence_score: float = 0.0
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    
    def get_impact_score(self) -> int:
        """Calculate impact score for prioritization."""
        impact_scores = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        return impact_scores.get(self.risk_impact, 0)
    
    def is_material(self) -> bool:
        """Check if this change is material (requires attention)."""
        return self.risk_impact in ["high", "critical"] or self.financial_impact is not None


class DriftDetection(BaseModel):
    """Complete drift detection result for a contract."""
    detection_id: str
    contract_id: str
    from_version_id: str
    to_version_id: str
    
    # Changes detected
    changes: List[DriftChange] = []
    
    # Summary
    total_changes: int = 0
    material_changes: int = 0
    high_risk_changes: int = 0
    
    # Status
    status: str = "completed"  # processing, completed, error
    processing_errors: List[str] = []
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_change(self, change: DriftChange) -> None:
        """Add a detected change."""
        self.changes.append(change)
        self.total_changes = len(self.changes)
        
        if change.is_material():
            self.material_changes += 1
        
        if change.risk_impact in ["high", "critical"]:
            self.high_risk_changes += 1
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[DriftChange]:
        """Get changes of a specific type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def get_material_changes(self) -> List[DriftChange]:
        """Get only material changes."""
        return [change for change in self.changes if change.is_material()]
    
    def get_high_risk_changes(self) -> List[DriftChange]:
        """Get only high-risk changes."""
        return [change for change in self.changes if change.risk_impact in ["high", "critical"]]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of detected changes."""
        return {
            "total_changes": self.total_changes,
            "material_changes": self.material_changes,
            "high_risk_changes": self.high_risk_changes,
            "change_types": {
                change_type.value: len(self.get_changes_by_type(change_type))
                for change_type in ChangeType
            },
            "risk_distribution": {
                "low": len([c for c in self.changes if c.risk_impact == "low"]),
                "medium": len([c for c in self.changes if c.risk_impact == "medium"]),
                "high": len([c for c in self.changes if c.risk_impact == "high"]),
                "critical": len([c for c in self.changes if c.risk_impact == "critical"]),
            }
        }
