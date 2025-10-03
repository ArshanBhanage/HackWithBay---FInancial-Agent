"""Alert and notification models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .obligation import SeverityLevel


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Status of alerts."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertType(str, Enum):
    """Types of alerts."""
    DRIFT_DETECTED = "drift_detected"
    RULE_VIOLATION = "rule_violation"
    CONFLICT_DETECTED = "conflict_detected"
    PROCESSING_ERROR = "processing_error"
    SYSTEM_ERROR = "system_error"


class Alert(BaseModel):
    """Alert model for contract drift and violations."""
    alert_id: str
    type: AlertType
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.NEW
    
    # Content
    title: str
    description: str
    details: Optional[Dict[str, Any]] = None
    
    # Related entities
    contract_id: Optional[str] = None
    version_id: Optional[str] = None
    rule_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    
    # Evidence and context
    evidence: Optional[Dict[str, Any]] = None
    affected_fields: List[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Resolution
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    
    # Notifications
    notification_sent: bool = False
    notification_channels: List[str] = []  # email, slack, webhook, etc.
    
    def acknowledge(self, user_id: str) -> None:
        """Acknowledge this alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def resolve(self, user_id: str, notes: Optional[str] = None) -> None:
        """Resolve this alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
    
    def dismiss(self, user_id: str, reason: Optional[str] = None) -> None:
        """Dismiss this alert."""
        self.status = AlertStatus.DISMISSED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        self.resolution_notes = reason
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if alert is still active (not resolved or dismissed)."""
        return self.status not in [AlertStatus.RESOLVED, AlertStatus.DISMISSED]
    
    def get_priority_score(self) -> int:
        """Calculate priority score for sorting."""
        severity_scores = {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4
        }
        
        # Base score from severity
        score = severity_scores.get(self.severity, 0)
        
        # Boost for new alerts
        if self.status == AlertStatus.NEW:
            score += 2
        
        # Boost for critical types
        if self.type == AlertType.CONFLICT_DETECTED:
            score += 1
        
        return score


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"


class Notification(BaseModel):
    """Notification sent for an alert."""
    notification_id: str
    alert_id: str
    channel: NotificationChannel
    recipient: str
    message: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "sent"  # sent, failed, pending
    error_message: Optional[str] = None
