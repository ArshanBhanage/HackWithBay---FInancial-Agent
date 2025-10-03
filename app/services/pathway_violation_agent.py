"""Pathway-based real-time violation detection agent."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

import pathway as pw

from ..models.policy import PolicyRule
from ..models.alert import Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class PathwayViolationAgent:
    """Real-time violation detection agent using Pathway streams."""
    
    def __init__(self):
        self.operational_data_table: Optional[pw.Table] = None
        self.policy_table: Optional[pw.Table] = None
        self.violation_stream: Optional[pw.Table] = None
        self.alert_stream: Optional[pw.Table] = None
        self._rules_loaded = False
    
    def setup_violation_detection_stream(self, operational_data: pw.Table, policies: pw.Table) -> pw.Table:
        """Set up real-time violation detection stream."""
        logger.info("Setting up Pathway violation detection stream")
        
        try:
            self.operational_data_table = operational_data
            self.policy_table = policies
            
            # Create violation detection pipeline
            violations = self._create_violation_pipeline(operational_data, policies)
            
            # Create alert stream from violations
            self.alert_stream = self._create_alert_stream(violations)
            
            logger.info("Pathway violation detection stream set up successfully")
            return self.alert_stream
            
        except Exception as e:
            logger.error(f"Failed to set up violation detection stream: {e}")
            raise
    
    def _create_violation_pipeline(self, operational_data: pw.Table, policies: pw.Table) -> pw.Table:
        """Create violation detection pipeline using Pathway operations."""
        
        # Join operational data with policies for rule checking
        # For now, we'll create a simple cross join since we need to restructure the data
        joined_data = operational_data.select(
            *pw.this,
            policy_rules=pw.apply(lambda _: [], pw.this.path),  # Placeholder for now
            policy_id=pw.apply(lambda _: "default_policy", pw.this.path)
        )
        
        # Apply rule validation logic
        violations = joined_data.select(
            *pw.this,
            violations=pw.apply(
                lambda op_data, rules: self._check_violations(op_data, rules),
                pw.this,
                pw.this.policy_rules
            )
        ).filter(
            pw.apply(lambda v: len(v) > 0, pw.this.violations)
        )
        
        return violations
    
    def _create_alert_stream(self, violations: pw.Table) -> pw.Table:
        """Create alert stream from violations."""
        
        # Explode violations to create individual alerts
        alerts = violations.select(
            alert_id=pw.apply(
                lambda v, entity_id: self._generate_alert_id(v, entity_id),
                pw.this.violations,
                pw.this.entity_id
            ),
            type="rule_violation",
            severity=pw.apply(
                lambda v: self._determine_severity(v),
                pw.this.violations
            ),
            title=pw.apply(
                lambda v: self._generate_alert_title(v),
                pw.this.violations
            ),
            description=pw.apply(
                lambda v: self._generate_alert_description(v),
                pw.this.violations
            ),
            contract_id=pw.this.path,
            created_at=pw.apply(lambda _: datetime.utcnow().isoformat() + "Z", pw.this.violations),
            status="new",
            rule_id=pw.apply(
                lambda v: self._extract_rule_id(v),
                pw.this.violations
            ),
            rule_type=pw.apply(
                lambda v: self._extract_rule_type(v),
                pw.this.violations
            ),
            expected_value=pw.apply(
                lambda v: self._extract_expected_value(v),
                pw.this.violations
            ),
            actual_value=pw.apply(
                lambda v: self._extract_actual_value(v),
                pw.this.violations
            ),
            entity_id=pw.this.entity_id,
            investor_name=pw.this.investor_name,
            evidence_doc=pw.this.path,
            evidence_page=pw.apply(lambda _: 1, pw.this.violations),
            evidence_snippet=pw.apply(
                lambda v: self._extract_evidence_snippet(v),
                pw.this.violations
            )
        )
        
        return alerts
    
    def _check_violations(self, operational_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check operational data against rules to find violations."""
        violations = []
        
        for rule in rules:
            try:
                # Extract rule details
                rule_type = rule.get('type', '')
                expected_value = rule.get('expected_value')
                basis = rule.get('basis', '')
                
                # Get actual value from operational data
                actual_value = self._extract_actual_value_from_data(operational_data, basis, rule_type)
                
                # Check for violations
                if self._is_violation(expected_value, actual_value, rule_type):
                    violation = {
                        'rule_id': rule.get('id', ''),
                        'rule_type': rule_type,
                        'expected_value': expected_value,
                        'actual_value': actual_value,
                        'basis': basis,
                        'severity': rule.get('severity', 'MEDIUM'),
                        'evidence': rule.get('evidence', {}),
                        'description': rule.get('description', ''),
                        'violation_type': self._determine_violation_type(expected_value, actual_value, rule_type)
                    }
                    violations.append(violation)
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule.get('id', 'unknown')}: {e}")
                continue
        
        return violations
    
    def _extract_actual_value_from_data(self, data: Dict[str, Any], basis: str, rule_type: str) -> Any:
        """Extract actual value from operational data based on rule basis."""
        # Map rule basis to data fields
        field_mapping = {
            'management_fee': ['fee_rate', 'management_fee', 'fee'],
            'reporting_requirement': ['reporting_deadline', 'deadline', 'days'],
            'allocation': ['sectors', 'investments', 'allocation'],
            'interest_rate': ['interest', 'rate'],
            'mfn_clause': ['mfn', 'most_favored_nation'],
            'covenant': ['covenant', 'requirement']
        }
        
        # Try to find the actual value
        possible_fields = field_mapping.get(basis, [basis])
        
        for field in possible_fields:
            if field in data:
                return data[field]
        
        # If not found, return None
        return None
    
    def _is_violation(self, expected: Any, actual: Any, rule_type: str) -> bool:
        """Determine if there's a violation based on expected vs actual values."""
        if actual is None:
            return False  # No data to compare
        
        try:
            if rule_type == 'fee.rate_percent':
                expected_float = float(expected) if expected is not None else 0
                actual_float = float(actual) if actual is not None else 0
                return abs(expected_float - actual_float) > 0.001  # Small tolerance for floating point
            
            elif rule_type == 'reporting.deadline_days':
                expected_int = int(expected) if expected is not None else 0
                actual_int = int(actual) if actual is not None else 0
                return actual_int > expected_int  # Violation if actual is more than expected
            
            elif rule_type == 'allocation.prohibited_sector':
                if isinstance(expected, list) and isinstance(actual, (list, str)):
                    if isinstance(actual, str):
                        actual_list = [actual]
                    else:
                        actual_list = actual
                    return any(sector in expected for sector in actual_list)
            
            elif rule_type == 'interest.rate_percent':
                expected_float = float(expected) if expected is not None else 0
                actual_float = float(actual) if actual is not None else 0
                return abs(expected_float - actual_float) > 0.001
            
            elif rule_type == 'mfn.notice_required':
                return expected != actual
            
            elif rule_type == 'covenant.requirement':
                return expected != actual
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing values: {e}")
            return False
        
        return False
    
    def _determine_violation_type(self, expected: Any, actual: Any, rule_type: str) -> str:
        """Determine the type of violation."""
        if rule_type == 'fee.rate_percent':
            if float(actual) > float(expected):
                return 'fee_exceeded'
            else:
                return 'fee_below_expected'
        elif rule_type == 'reporting.deadline_days':
            return 'deadline_exceeded'
        elif rule_type == 'allocation.prohibited_sector':
            return 'prohibited_investment'
        else:
            return 'rule_violation'
    
    def _generate_alert_id(self, violations: List[Dict[str, Any]], entity_id: str) -> str:
        """Generate unique alert ID."""
        import hashlib
        import time
        
        if violations:
            rule_id = violations[0].get('rule_id', 'unknown')
            content = f"{rule_id}_{entity_id}_{time.time()}"
            return hashlib.md5(content.encode()).hexdigest()[:16]
        return f"alert_{int(time.time())}"
    
    def _determine_severity(self, violations: List[Dict[str, Any]]) -> str:
        """Determine alert severity from violations."""
        if not violations:
            return 'LOW'
        
        severities = [v.get('severity', 'MEDIUM') for v in violations]
        
        if 'HIGH' in severities:
            return 'HIGH'
        elif 'MEDIUM' in severities:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_alert_title(self, violations: List[Dict[str, Any]]) -> str:
        """Generate alert title from violations."""
        if not violations:
            return 'Unknown Violation'
        
        violation = violations[0]
        rule_type = violation.get('rule_type', 'unknown')
        
        if rule_type == 'fee.rate_percent':
            return 'Management Fee Violation'
        elif rule_type == 'reporting.deadline_days':
            return 'Reporting Deadline Violation'
        elif rule_type == 'allocation.prohibited_sector':
            return 'Prohibited Investment Violation'
        else:
            return f'Rule Violation: {rule_type}'
    
    def _generate_alert_description(self, violations: List[Dict[str, Any]]) -> str:
        """Generate alert description from violations."""
        if not violations:
            return 'No description available'
        
        violation = violations[0]
        rule_type = violation.get('rule_type', 'unknown')
        expected = violation.get('expected_value')
        actual = violation.get('actual_value')
        
        return f'Violation detected: Expected {expected}, Actual {actual} for {rule_type}'
    
    def _extract_rule_id(self, violations: List[Dict[str, Any]]) -> str:
        """Extract rule ID from violations."""
        return violations[0].get('rule_id', 'unknown') if violations else 'unknown'
    
    def _extract_rule_type(self, violations: List[Dict[str, Any]]) -> str:
        """Extract rule type from violations."""
        return violations[0].get('rule_type', 'unknown') if violations else 'unknown'
    
    def _extract_expected_value(self, violations: List[Dict[str, Any]]) -> str:
        """Extract expected value from violations."""
        return str(violations[0].get('expected_value', 'N/A')) if violations else 'N/A'
    
    def _extract_actual_value(self, violations: List[Dict[str, Any]]) -> str:
        """Extract actual value from violations."""
        return str(violations[0].get('actual_value', 'N/A')) if violations else 'N/A'
    
    def _extract_evidence_snippet(self, violations: List[Dict[str, Any]]) -> str:
        """Extract evidence snippet from violations."""
        if violations:
            evidence = violations[0].get('evidence', {})
            return evidence.get('snippet', 'No evidence available')
        return 'No evidence available'
    
    async def start_violation_monitoring(self) -> None:
        """Start real-time violation monitoring."""
        logger.info("Starting Pathway violation monitoring")
        
        try:
            if self.alert_stream:
                # Set up output to database or API
                await self._setup_alert_output()
                logger.info("Violation monitoring started successfully")
            else:
                logger.warning("No alert stream available for monitoring")
                
        except Exception as e:
            logger.error(f"Failed to start violation monitoring: {e}")
            raise
    
    async def _setup_alert_output(self) -> None:
        """Set up alert output to database or external systems."""
        # This would integrate with your database service
        # For now, we'll just log the alerts
        pass
