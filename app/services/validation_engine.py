"""Validation engine for continuous contract compliance monitoring."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

import pathway as pw

from ..models.policy import Policy, PolicyRule
from ..models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from ..models.obligation import SeverityLevel, EnforcementAction

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Engine for continuous validation of contract compliance."""
    
    def __init__(self):
        self.active_policies: Dict[str, Policy] = {}
        self.validation_rules: Dict[str, List[PolicyRule]] = {}
        self.operational_data_table: Optional[pw.Table] = None
        self.alert_table: Optional[pw.Table] = None
        self._validation_callbacks: List[callable] = []
    
    def load_policy(self, policy: Policy) -> None:
        """Load a policy for validation."""
        logger.info(f"Loading policy {policy.policy_id}")
        
        self.active_policies[policy.policy_id] = policy
        
        # Group rules by trigger event
        for rule in policy.rules:
            trigger = rule.enforcement.get("when", "on_event")
            if trigger not in self.validation_rules:
                self.validation_rules[trigger] = []
            self.validation_rules[trigger].append(rule)
        
        logger.info(f"Policy loaded: {len(policy.rules)} rules across {len(self.validation_rules)} triggers")
    
    def setup_operational_data_stream(self, data_table: pw.Table) -> None:
        """Set up operational data stream for validation."""
        self.operational_data_table = data_table
        
        # Set up validation pipeline
        self._setup_validation_pipeline()
    
    def _setup_validation_pipeline(self) -> None:
        """Set up the validation pipeline using Pathway."""
        if not self.operational_data_table:
            logger.warning("No operational data table set up")
            return
        
        # Create validation results table
        validation_results = self.operational_data_table.select(
            *self.operational_data_table,
            validation_status="pending",
            validation_errors=[],
            validation_timestamp=datetime.utcnow(),
            severity="LOW"
        )
        
        # Apply validation rules
        for trigger, rules in self.validation_rules.items():
            validation_results = self._apply_validation_rules(validation_results, rules, trigger)
        
        # Generate alerts for violations
        self.alert_table = self._generate_alerts(validation_results)
        
        logger.info("Validation pipeline set up successfully")
    
    def _apply_validation_rules(self, data_table: pw.Table, rules: List[PolicyRule], trigger: str) -> pw.Table:
        """Apply validation rules to data table."""
        # This is a simplified implementation
        # In practice, this would involve complex joins and rule evaluation
        
        for rule in rules:
            data_table = self._apply_single_rule(data_table, rule)
        
        return data_table
    
    def _apply_single_rule(self, data_table: pw.Table, rule: PolicyRule) -> pw.Table:
        """Apply a single validation rule."""
        # Create rule validation logic
        rule_validation = pw.apply_with_type(
            lambda row: self._validate_rule(row, rule),
            dict,
            data_table
        )
        
        # Update data table with validation results
        data_table = data_table.select(
            *data_table,
            rule_validation=rule_validation
        )
        
        return data_table
    
    def _validate_rule(self, data_row: Dict[str, Any], rule: PolicyRule) -> Dict[str, Any]:
        """Validate a single rule against data row."""
        try:
            # Extract relevant field from data
            field_value = self._extract_field_value(data_row, rule)
            
            # Perform validation
            is_valid, error_message = self._check_rule_compliance(rule, field_value)
            
            return {
                "rule_id": rule.id,
                "is_valid": is_valid,
                "error_message": error_message,
                "expected_value": rule.expected_value,
                "actual_value": field_value,
                "severity": rule.severity.value
            }
            
        except Exception as e:
            logger.error(f"Error validating rule {rule.id}: {e}")
            return {
                "rule_id": rule.id,
                "is_valid": False,
                "error_message": f"Validation error: {str(e)}",
                "expected_value": rule.expected_value,
                "actual_value": None,
                "severity": rule.severity.value
            }
    
    def _extract_field_value(self, data_row: Dict[str, Any], rule: PolicyRule) -> Any:
        """Extract field value from data row based on rule."""
        # Map rule basis to data field
        field_mapping = {
            "management_fee": "fee_rate",
            "interest_rate": "interest_rate",
            "reporting_requirement": "reporting_deadline",
            "maturity_date": "maturity_date"
        }
        
        field_name = field_mapping.get(rule.basis, rule.basis)
        return data_row.get(field_name)
    
    def _check_rule_compliance(self, rule: PolicyRule, actual_value: Any) -> Tuple[bool, Optional[str]]:
        """Check if actual value complies with rule."""
        if actual_value is None:
            return False, f"Required field {rule.basis} is missing"
        
        # Type-specific validation
        if rule.type == "fee.rate_percent":
            return self._validate_percentage(rule.expected_value, actual_value, rule.basis)
        elif rule.type == "reporting.deadline_days":
            return self._validate_deadline(rule.expected_value, actual_value, rule.basis)
        elif rule.type == "maturity.date":
            return self._validate_date(rule.expected_value, actual_value, rule.basis)
        else:
            return self._validate_generic(rule.expected_value, actual_value, rule.basis)
    
    def _validate_percentage(self, expected: float, actual: float, field_name: str) -> Tuple[bool, Optional[str]]:
        """Validate percentage values."""
        tolerance = 0.01  # 1% tolerance
        if abs(expected - actual) > tolerance:
            return False, f"{field_name} mismatch: expected {expected}%, got {actual}%"
        return True, None
    
    def _validate_deadline(self, expected: int, actual: int, field_name: str) -> Tuple[bool, Optional[str]]:
        """Validate deadline values."""
        if actual > expected:
            return False, f"{field_name} exceeded: expected {expected} days, got {actual} days"
        return True, None
    
    def _validate_date(self, expected: str, actual: str, field_name: str) -> Tuple[bool, Optional[str]]:
        """Validate date values."""
        if actual != expected:
            return False, f"{field_name} mismatch: expected {expected}, got {actual}"
        return True, None
    
    def _validate_generic(self, expected: Any, actual: Any, field_name: str) -> Tuple[bool, Optional[str]]:
        """Generic validation."""
        if actual != expected:
            return False, f"{field_name} mismatch: expected {expected}, got {actual}"
        return True, None
    
    def _generate_alerts(self, validation_results: pw.Table) -> pw.Table:
        """Generate alerts from validation results."""
        # Filter for violations
        violations = validation_results.filter(
            pw.this.validation_status == "violation"
        )
        
        # Create alerts
        alerts = violations.select(
            alert_id=pw.apply_with_type(
                lambda row: self._generate_alert_id(row),
                str,
                violations
            ),
            type="rule_violation",
            severity=pw.this.severity,
            title=pw.apply_with_type(
                lambda row: f"Rule Violation: {row.get('rule_id', 'unknown')}",
                str,
                violations
            ),
            description=pw.this.rule_validation.error_message,
            contract_id=pw.this.contract_id,
            created_at=datetime.utcnow(),
            status="new"
        )
        
        return alerts
    
    def _generate_alert_id(self, row: Dict[str, Any]) -> str:
        """Generate unique alert ID."""
        import hashlib
        content = f"{row.get('rule_id', 'unknown')}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def add_validation_callback(self, callback: callable) -> None:
        """Add a callback for validation events."""
        self._validation_callbacks.append(callback)
    
    async def validate_operational_data(self, data: Dict[str, Any]) -> List[Alert]:
        """Validate operational data against active policies."""
        alerts = []
        
        for policy_id, policy in self.active_policies.items():
            policy_alerts = await self._validate_against_policy(data, policy)
            alerts.extend(policy_alerts)
        
        # Execute callbacks
        for callback in self._validation_callbacks:
            try:
                await callback(alerts)
            except Exception as e:
                logger.error(f"Error in validation callback: {e}")
        
        return alerts
    
    async def _validate_against_policy(self, data: Dict[str, Any], policy: Policy) -> List[Alert]:
        """Validate data against a specific policy."""
        alerts = []
        
        for rule in policy.rules:
            try:
                # Check if rule applies to this data
                if not self._rule_applies_to_data(rule, data):
                    continue
                
                # Validate rule
                is_valid, error_message = await self._validate_single_rule(rule, data)
                
                if not is_valid:
                    alert = self._create_violation_alert(rule, data, error_message)
                    alerts.append(alert)
                    
            except Exception as e:
                logger.error(f"Error validating rule {rule.id}: {e}")
                alert = self._create_error_alert(rule, data, str(e))
                alerts.append(alert)
        
        return alerts
    
    def _rule_applies_to_data(self, rule: PolicyRule, data: Dict[str, Any]) -> bool:
        """Check if rule applies to the given data."""
        # Check entity applicability
        if rule.applies_to != "ALL_INVESTORS":
            if isinstance(rule.applies_to, list):
                if data.get("entity_id") not in rule.applies_to:
                    return False
            elif data.get("entity_id") != rule.applies_to:
                return False
        
        # Check effective period
        if not self._rule_is_effective(rule, data.get("timestamp", datetime.utcnow())):
            return False
        
        return True
    
    def _rule_is_effective(self, rule: PolicyRule, timestamp: datetime) -> bool:
        """Check if rule is effective at given timestamp."""
        start_date = rule.effective_period.get("start")
        end_date = rule.effective_period.get("end")
        
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if timestamp < start:
                return False
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if timestamp > end:
                return False
        
        return True
    
    async def _validate_single_rule(self, rule: PolicyRule, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate a single rule against data."""
        # Extract field value
        field_value = self._extract_field_value(data, rule)
        
        # Perform validation
        return self._check_rule_compliance(rule, field_value)
    
    def _create_violation_alert(self, rule: PolicyRule, data: Dict[str, Any], error_message: str) -> Alert:
        """Create alert for rule violation."""
        return Alert(
            alert_id=f"violation_{rule.id}_{datetime.utcnow().timestamp()}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity(rule.severity.value),
            title=f"Rule Violation: {rule.id}",
            description=error_message,
            contract_id=data.get("contract_id"),
            rule_id=rule.id,
            details={
                "rule_type": rule.type,
                "expected_value": rule.expected_value,
                "actual_value": data.get(rule.basis),
                "data": data
            },
            evidence=rule.evidence
        )
    
    def _create_error_alert(self, rule: PolicyRule, data: Dict[str, Any], error_message: str) -> Alert:
        """Create alert for validation error."""
        return Alert(
            alert_id=f"error_{rule.id}_{datetime.utcnow().timestamp()}",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.MEDIUM,
            title=f"Validation Error: {rule.id}",
            description=error_message,
            contract_id=data.get("contract_id"),
            rule_id=rule.id,
            details={
                "rule_type": rule.type,
                "data": data,
                "error": error_message
            }
        )
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation status."""
        return {
            "active_policies": len(self.active_policies),
            "total_rules": sum(len(rules) for rules in self.validation_rules.values()),
            "validation_triggers": list(self.validation_rules.keys()),
            "callbacks_registered": len(self._validation_callbacks)
        }
    
    def remove_policy(self, policy_id: str) -> None:
        """Remove a policy from validation."""
        if policy_id in self.active_policies:
            del self.active_policies[policy_id]
            
            # Remove rules from validation_rules
            for trigger, rules in self.validation_rules.items():
                self.validation_rules[trigger] = [
                    rule for rule in rules 
                    if not rule.id.startswith(f"{policy_id}_")
                ]
            
            logger.info(f"Policy {policy_id} removed from validation")
    
    def start_validation_stream(self) -> None:
        """Start the validation stream."""
        if self.alert_table:
            # Output alerts to file
            pw.io.csv.write(
                self.alert_table,
                "./streaming_output/alerts.csv"
            )
            
            logger.info("Validation stream started")
        else:
            logger.warning("No alert table set up for streaming")
