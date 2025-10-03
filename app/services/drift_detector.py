"""Drift detection service for contract changes."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json
from difflib import SequenceMatcher

from ..models.contract import Contract, ContractVersion, ContractField
from ..models.drift import DriftDetection, DriftChange, ChangeType
from ..models.alert import Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class DriftDetector:
    """Service for detecting changes and drift in financial contracts."""
    
    def __init__(self):
        self.similarity_threshold = 0.8
        self.material_change_threshold = 0.1  # 10% change threshold for material changes
    
    async def detect_drift(self, contract: Contract, from_version_id: str, to_version_id: str) -> DriftDetection:
        """Detect drift between two contract versions."""
        logger.info(f"Detecting drift for contract {contract.contract_id} from {from_version_id} to {to_version_id}")
        
        # Get versions
        from_version = contract.get_version_by_id(from_version_id)
        to_version = contract.get_version_by_id(to_version_id)
        
        if not from_version or not to_version:
            raise ValueError("One or both versions not found")
        
        # Create drift detection result
        detection = DriftDetection(
            detection_id=self._generate_detection_id(contract.contract_id, from_version_id, to_version_id),
            contract_id=contract.contract_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id
        )
        
        try:
            # Detect field-level changes
            field_changes = await self._detect_field_changes(from_version, to_version)
            for change in field_changes:
                detection.add_change(change)
            
            # Detect structural changes
            structural_changes = await self._detect_structural_changes(from_version, to_version)
            for change in structural_changes:
                detection.add_change(change)
            
            # Detect table changes
            table_changes = await self._detect_table_changes(from_version, to_version)
            for change in table_changes:
                detection.add_change(change)
            
            # Detect clause changes
            clause_changes = await self._detect_clause_changes(from_version, to_version)
            for change in clause_changes:
                detection.add_change(change)
            
            detection.status = "completed"
            detection.completed_at = datetime.utcnow()
            
            logger.info(f"Drift detection completed: {detection.total_changes} changes found")
            return detection
            
        except Exception as e:
            logger.error(f"Error in drift detection: {e}")
            detection.status = "error"
            detection.processing_errors.append(str(e))
            return detection
    
    async def _detect_field_changes(self, from_version: ContractVersion, to_version: ContractVersion) -> List[DriftChange]:
        """Detect changes in extracted fields."""
        changes = []
        
        # Create field maps for comparison
        from_fields = {field.field_name: field for field in from_version.extracted_fields}
        to_fields = {field.field_name: field for field in to_version.extracted_fields}
        
        # Check for added fields
        for field_name, field in to_fields.items():
            if field_name not in from_fields:
                change = DriftChange(
                    change_id=self._generate_change_id(field_name, "added"),
                    change_type=ChangeType.FIELD_ADDED,
                    field_name=field_name,
                    new_value=field.value,
                    page_number=field.page_number,
                    text_snippet=field.text_snippet,
                    table_cell=field.table_cell,
                    risk_impact=self._assess_field_risk_impact(field_name, None, field.value),
                    evidence={"field": field.dict()},
                    confidence_score=field.confidence
                )
                changes.append(change)
        
        # Check for removed fields
        for field_name, field in from_fields.items():
            if field_name not in to_fields:
                change = DriftChange(
                    change_id=self._generate_change_id(field_name, "removed"),
                    change_type=ChangeType.FIELD_REMOVED,
                    field_name=field_name,
                    old_value=field.value,
                    page_number=field.page_number,
                    text_snippet=field.text_snippet,
                    table_cell=field.table_cell,
                    risk_impact=self._assess_field_risk_impact(field_name, field.value, None),
                    evidence={"field": field.dict()},
                    confidence_score=field.confidence
                )
                changes.append(change)
        
        # Check for modified fields
        for field_name in from_fields:
            if field_name in to_fields:
                from_field = from_fields[field_name]
                to_field = to_fields[field_name]
                
                if not self._values_equal(from_field.value, to_field.value):
                    change = DriftChange(
                        change_id=self._generate_change_id(field_name, "modified"),
                        change_type=ChangeType.FIELD_MODIFIED,
                        field_name=field_name,
                        old_value=from_field.value,
                        new_value=to_field.value,
                        page_number=to_field.page_number,
                        text_snippet=to_field.text_snippet,
                        table_cell=to_field.table_cell,
                        risk_impact=self._assess_field_risk_impact(field_name, from_field.value, to_field.value),
                        financial_impact=self._calculate_financial_impact(field_name, from_field.value, to_field.value),
                        evidence={
                            "from_field": from_field.dict(),
                            "to_field": to_field.dict()
                        },
                        confidence_score=min(from_field.confidence, to_field.confidence)
                    )
                    changes.append(change)
        
        return changes
    
    async def _detect_structural_changes(self, from_version: ContractVersion, to_version: ContractVersion) -> List[DriftChange]:
        """Detect structural changes in documents."""
        changes = []
        
        # Compare page counts
        if from_version.page_count != to_version.page_count:
            change = DriftChange(
                change_id=self._generate_change_id("page_count", "structural"),
                change_type=ChangeType.STRUCTURAL_CHANGE,
                field_name="page_count",
                old_value=from_version.page_count,
                new_value=to_version.page_count,
                risk_impact="medium",
                evidence={
                    "description": "Document page count changed",
                    "from_pages": from_version.page_count,
                    "to_pages": to_version.page_count
                }
            )
            changes.append(change)
        
        # Compare file sizes
        size_change_percent = abs(to_version.file_size - from_version.file_size) / from_version.file_size
        if size_change_percent > 0.1:  # 10% size change
            change = DriftChange(
                change_id=self._generate_change_id("file_size", "structural"),
                change_type=ChangeType.STRUCTURAL_CHANGE,
                field_name="file_size",
                old_value=from_version.file_size,
                new_value=to_version.file_size,
                risk_impact="low" if size_change_percent < 0.5 else "medium",
                evidence={
                    "description": "Document file size changed significantly",
                    "change_percent": size_change_percent
                }
            )
            changes.append(change)
        
        return changes
    
    async def _detect_table_changes(self, from_version: ContractVersion, to_version: ContractVersion) -> List[DriftChange]:
        """Detect changes in table data."""
        changes = []
        
        # Group fields by table
        from_tables = self._group_fields_by_table(from_version.extracted_fields)
        to_tables = self._group_fields_by_table(to_version.extracted_fields)
        
        # Compare tables
        for table_name in set(list(from_tables.keys()) + list(to_tables.keys())):
            from_table_fields = from_tables.get(table_name, [])
            to_table_fields = to_tables.get(table_name, [])
            
            if not from_table_fields and to_table_fields:
                # Table added
                change = DriftChange(
                    change_id=self._generate_change_id(table_name, "table_added"),
                    change_type=ChangeType.TABLE_ADDED,
                    field_name=table_name,
                    new_value=f"Table with {len(to_table_fields)} fields",
                    risk_impact="medium",
                    evidence={"table_fields": [f.dict() for f in to_table_fields]}
                )
                changes.append(change)
            elif from_table_fields and not to_table_fields:
                # Table removed
                change = DriftChange(
                    change_id=self._generate_change_id(table_name, "table_removed"),
                    change_type=ChangeType.TABLE_REMOVED,
                    field_name=table_name,
                    old_value=f"Table with {len(from_table_fields)} fields",
                    risk_impact="high",
                    evidence={"table_fields": [f.dict() for f in from_table_fields]}
                )
                changes.append(change)
            elif from_table_fields and to_table_fields:
                # Table modified
                table_changes = self._compare_table_fields(from_table_fields, to_table_fields, table_name)
                changes.extend(table_changes)
        
        return changes
    
    async def _detect_clause_changes(self, from_version: ContractVersion, to_version: ContractVersion) -> List[DriftChange]:
        """Detect changes in contract clauses."""
        changes = []
        
        # This would involve more sophisticated text analysis
        # For now, we'll do a simple comparison of text snippets
        
        from_snippets = [field.text_snippet for field in from_version.extracted_fields if field.text_snippet]
        to_snippets = [field.text_snippet for field in to_version.extracted_fields if field.text_snippet]
        
        # Find similar snippets that have changed
        for to_snippet in to_snippets:
            best_match = None
            best_similarity = 0
            
            for from_snippet in from_snippets:
                similarity = SequenceMatcher(None, from_snippet, to_snippet).ratio()
                if similarity > best_similarity and similarity < 1.0:
                    best_similarity = similarity
                    best_match = from_snippet
            
            if best_match and best_similarity > self.similarity_threshold:
                change = DriftChange(
                    change_id=self._generate_change_id("clause", "modified"),
                    change_type=ChangeType.CLAUSE_MODIFIED,
                    old_value=best_match,
                    new_value=to_snippet,
                    risk_impact=self._assess_text_risk_impact(best_match, to_snippet),
                    evidence={
                        "similarity": best_similarity,
                        "from_text": best_match,
                        "to_text": to_snippet
                    },
                    confidence_score=best_similarity
                )
                changes.append(change)
        
        return changes
    
    def _group_fields_by_table(self, fields: List[ContractField]) -> Dict[str, List[ContractField]]:
        """Group fields by table name."""
        tables = {}
        for field in fields:
            if field.table_cell:
                # Extract table name from field name (assuming format: table_name_row_col)
                table_name = field.field_name.split('_')[0] if '_' in field.field_name else "unknown_table"
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append(field)
        return tables
    
    def _compare_table_fields(self, from_fields: List[ContractField], to_fields: List[ContractField], table_name: str) -> List[DriftChange]:
        """Compare fields within a table."""
        changes = []
        
        # Create field maps by position
        from_positions = {f.table_cell: f for f in from_fields if f.table_cell}
        to_positions = {f.table_cell: f for f in to_fields if f.table_cell}
        
        # Check for changes in existing positions
        for position in set(list(from_positions.keys()) + list(to_positions.keys())):
            from_field = from_positions.get(position)
            to_field = to_positions.get(position)
            
            if from_field and to_field:
                if not self._values_equal(from_field.value, to_field.value):
                    change = DriftChange(
                        change_id=self._generate_change_id(f"{table_name}_{position}", "table_modified"),
                        change_type=ChangeType.TABLE_MODIFIED,
                        field_name=f"{table_name}_{position}",
                        old_value=from_field.value,
                        new_value=to_field.value,
                        table_cell=position,
                        risk_impact=self._assess_field_risk_impact(field_name, from_field.value, to_field.value),
                        evidence={
                            "table_name": table_name,
                            "position": position,
                            "from_field": from_field.dict(),
                            "to_field": to_field.dict()
                        }
                    )
                    changes.append(change)
        
        return changes
    
    def _values_equal(self, value1: Any, value2: Any) -> bool:
        """Check if two values are equal, handling different types."""
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False
        
        # Convert to strings for comparison
        str1 = str(value1).strip().lower()
        str2 = str(value2).strip().lower()
        
        return str1 == str2
    
    def _assess_field_risk_impact(self, field_name: str, old_value: Any, new_value: Any) -> str:
        """Assess risk impact of a field change."""
        # High-risk fields
        high_risk_fields = [
            "interest_rate", "management_fee_rate", "carried_interest",
            "maturity_date", "covenant", "collateral", "guarantee"
        ]
        
        # Medium-risk fields
        medium_risk_fields = [
            "reporting_deadline", "notice_period", "termination_clause",
            "amendment_procedure", "governing_law"
        ]
        
        field_lower = field_name.lower()
        
        if any(risk_field in field_lower for risk_field in high_risk_fields):
            return "high"
        elif any(risk_field in field_lower for risk_field in medium_risk_fields):
            return "medium"
        else:
            return "low"
    
    def _assess_text_risk_impact(self, old_text: str, new_text: str) -> str:
        """Assess risk impact of text changes."""
        # Look for high-risk keywords
        high_risk_keywords = [
            "interest", "fee", "payment", "default", "breach", "penalty",
            "termination", "covenant", "collateral", "guarantee"
        ]
        
        text_lower = (old_text + " " + new_text).lower()
        
        if any(keyword in text_lower for keyword in high_risk_keywords):
            return "high"
        else:
            return "medium"
    
    def _calculate_financial_impact(self, field_name: str, old_value: Any, new_value: Any) -> Optional[float]:
        """Calculate financial impact of a change."""
        try:
            # Only calculate for numeric fields
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                if old_value != 0:
                    return abs((new_value - old_value) / old_value) * 100  # Percentage change
                else:
                    return abs(new_value) if new_value != 0 else 0
        except (TypeError, ValueError, ZeroDivisionError):
            pass
        
        return None
    
    def _generate_detection_id(self, contract_id: str, from_version: str, to_version: str) -> str:
        """Generate unique detection ID."""
        content = f"{contract_id}_{from_version}_{to_version}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_change_id(self, field_name: str, change_type: str) -> str:
        """Generate unique change ID."""
        content = f"{field_name}_{change_type}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def create_drift_alert(self, detection: DriftDetection) -> Alert:
        """Create an alert for detected drift."""
        severity = AlertSeverity.HIGH if detection.high_risk_changes > 0 else AlertSeverity.MEDIUM
        
        return Alert(
            alert_id=f"drift_{detection.detection_id}",
            type=AlertType.DRIFT_DETECTED,
            severity=severity,
            title=f"Contract Drift Detected: {detection.contract_id}",
            description=f"Found {detection.total_changes} changes, {detection.material_changes} material",
            contract_id=detection.contract_id,
            version_id=detection.to_version_id,
            details={
                "detection_id": detection.detection_id,
                "from_version": detection.from_version_id,
                "to_version": detection.to_version_id,
                "summary": detection.get_summary()
            },
            affected_fields=[change.field_name for change in detection.changes if change.field_name]
        )
