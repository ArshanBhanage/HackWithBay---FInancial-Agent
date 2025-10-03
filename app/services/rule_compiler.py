"""Rule compiler service for processing document candidates into enforceable rules."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import hashlib

from ..models.policy import Policy, PolicyRule, RuleType
from ..models.obligation import SeverityLevel

logger = logging.getLogger(__name__)


class RuleCompiler:
    """Compiles document candidates into enforceable validation rules."""
    
    # Document class priority for precedence resolution
    DOC_PRIORITY = {
        "Amendment": 3, 
        "Rider": 3,
        "SideLetter": 2,
        "LPA": 1, 
        "CreditAgreement": 1, 
        "Policy": 1,
        "RegulatoryFiling": 1
    }
    
    def __init__(self):
        self.compiled_rules: Dict[str, PolicyRule] = {}
        self.rule_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def compile_rules(self, candidates: List[Dict[str, Any]], now: Optional[datetime] = None) -> List[PolicyRule]:
        """
        Compile document candidates into enforceable rules.
        
        Args:
            candidates: List of rule candidates extracted from documents
            now: Current timestamp for effective period validation
            
        Returns:
            List of compiled PolicyRule objects
        """
        now = now or datetime.utcnow()
        buckets = defaultdict(list)
        
        logger.info(f"Compiling {len(candidates)} candidates into rules")
        
        # Group candidates by rule key
        for candidate in candidates:
            rule_key = self._create_rule_key(candidate)
            buckets[rule_key].append(candidate)
        
        compiled = []
        conflicts = []
        
        # Process each rule key group
        for rule_key, items in buckets.items():
            try:
                rule, history, conflict = self._compile_rule_group(rule_key, items, now)
                compiled.append(rule)
                self.rule_history[rule.id] = history
                if conflict:
                    conflicts.append(conflict)
            except Exception as e:
                logger.error(f"Error compiling rule group {rule_key}: {e}")
        
        # Log conflicts for human review
        if conflicts:
            logger.warning(f"Found {len(conflicts)} rule conflicts requiring review")
            for conflict in conflicts:
                logger.warning(f"Conflict: {conflict}")
        
        logger.info(f"Compiled {len(compiled)} rules from {len(candidates)} candidates")
        return compiled
    
    def _create_rule_key(self, candidate: Dict[str, Any]) -> Tuple:
        """Create a stable rule key for grouping candidates."""
        applies_to = candidate.get("applies_to", "ALL_INVESTORS")
        if isinstance(applies_to, list):
            applies_to = tuple(sorted(applies_to))
        
        rule_type = candidate.get("type", "unknown")
        basis = candidate.get("basis", rule_type)
        scope = candidate.get("scope", [])
        
        # Handle scope - convert lists to tuple of strings
        if isinstance(scope, list):
            scope_tuple = tuple(sorted(str(item) for item in scope))
        else:
            scope_tuple = (str(scope),) if scope else ()
        return (applies_to, rule_type, basis, scope_tuple)
    
    def _compile_rule_group(self, rule_key: Tuple, items: List[Dict[str, Any]], now: datetime) -> Tuple[PolicyRule, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Compile a group of candidates with the same rule key."""
        applies_to, rule_type, basis, scope = rule_key
        
        # Normalize and sort items by precedence
        for item in items:
            item["_start"] = self._parse_effective_date(item.get("effective_date"))
            item["_prio"] = self.DOC_PRIORITY.get(item.get("doc_class", ""), 0)
        
        # Sort by (start date desc, priority desc) - most recent and highest priority first
        items.sort(key=lambda x: (x["_start"], x["_prio"]), reverse=True)
        
        # Build history segments
        history = []
        seen = set()
        conflict = None
        
        for item in items:
            seg = {
                "expected_value": item.get("expected_value"),
                "start": item["_start"].isoformat() + "Z",
                "doc_class": item.get("doc_class"),
                "doc_id": item.get("doc_id"),
                "evidence": item.get("evidence", {}),
                "exceptions": item.get("exceptions", []),
                "trigger": item.get("trigger", "on_event"),
            }
            
            # Check for conflicts (same effective period, different values)
            if not conflict:
                for existing_seg in history:
                    if (existing_seg["start"] == seg["start"] and 
                        existing_seg["expected_value"] != seg["expected_value"]):
                        conflict = {
                            "rule_key": rule_key,
                            "conflicting_values": [existing_seg["expected_value"], seg["expected_value"]],
                            "effective_date": seg["start"],
                            "documents": [existing_seg["doc_id"], seg["doc_id"]]
                        }
                        break
            
            # Avoid duplicate history entries
            # Convert expected_value to string if it's a list for hashing
            expected_val = seg["expected_value"]
            if isinstance(expected_val, list):
                expected_val = str(sorted(expected_val))
            sig = (expected_val, seg["start"], seg["doc_class"])
            if sig not in seen:
                history.append(seg)
                seen.add(sig)
        
        # Active rule is the first item after sorting (highest precedence)
        active = items[0]
        
        # Create rule ID
        rule_id = self._generate_rule_id(rule_key)
        
        # Create PolicyRule object
        rule = PolicyRule(
            id=rule_id,
            type=RuleType(rule_type),
            applies_to=list(applies_to) if isinstance(applies_to, tuple) else applies_to,
            expected_value=active.get("expected_value"),
            basis=basis,
            effective_period={
                "start": active["_start"].isoformat() + "Z",
                "end": None
            },
            evidence=active.get("evidence", {}),
            severity=self._determine_severity(rule_type, active),
            enforcement=active.get("enforcement", {"when": "on_event", "action": "alert"}),
            exceptions=active.get("exceptions", []),
            metadata={
                "compiled_at": now.isoformat() + "Z",
                "source_documents": [item.get("doc_id") for item in items],
                "conflict": conflict is not None
            }
        )
        
        return rule, history, conflict
    
    def _parse_effective_date(self, date_str: Optional[str]) -> datetime:
        """Parse effective date string to datetime."""
        if not date_str:
            return datetime.min
        
        try:
            # Handle ISO format with or without Z
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            logger.warning(f"Could not parse effective date: {date_str}")
            return datetime.min
    
    def _generate_rule_id(self, rule_key: Tuple) -> str:
        """Generate stable rule ID from rule key."""
        raw = "|".join([str(k) for k in rule_key])
        return "R_" + hashlib.md5(raw.encode()).hexdigest()[:10]
    
    def _determine_severity(self, rule_type: str, candidate: Dict[str, Any]) -> SeverityLevel:
        """Determine severity level for a rule."""
        # High severity for critical financial terms
        if rule_type in ["fee.rate_percent", "allocation.prohibited_sector", "interest.rate_percent"]:
            return SeverityLevel.HIGH
        
        # Medium severity for operational requirements
        if rule_type in ["reporting.deadline_days", "mfn.notice_required", "covenant.requirement"]:
            return SeverityLevel.MEDIUM
        
        # Default to LOW
        return SeverityLevel.LOW
    
    def create_policy_from_rules(self, rules: List[PolicyRule], policy_id: str) -> Policy:
        """Create a Policy object from compiled rules."""
        return Policy(
            policy_id=policy_id,
            name=f"Policy from {policy_id}",
            version="1.0.0",
            description=f"Compiled policy with {len(rules)} rules",
            generated_at=datetime.utcnow(),
            source_documents=[],  # Will be populated from rule metadata
            rules=rules,
            status="compiled"
        )
    
    def get_rule_history(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get historical changes for a rule."""
        return self.rule_history.get(rule_id, [])
    
    def find_conflicting_rules(self, new_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find potential conflicts with existing rules."""
        conflicts = []
        
        for candidate in new_candidates:
            rule_key = self._create_rule_key(candidate)
            
            # Check if we already have a rule for this key
            for existing_rule_id, existing_rule in self.compiled_rules.items():
                existing_key = self._create_rule_key({
                    "applies_to": existing_rule.applies_to,
                    "type": existing_rule.type.value,
                    "basis": existing_rule.basis,
                    "scope": []
                })
                
                if rule_key == existing_key:
                    # Check for value conflicts
                    if existing_rule.expected_value != candidate.get("expected_value"):
                        conflicts.append({
                            "rule_id": existing_rule_id,
                            "new_candidate": candidate,
                            "existing_value": existing_rule.expected_value,
                            "new_value": candidate.get("expected_value")
                        })
        
        return conflicts


# Example usage and candidate extraction helpers
def create_candidate_from_document(
    doc_id: str,
    doc_class: str,
    effective_date: str,
    applies_to: str | List[str],
    rule_type: str,
    basis: str,
    expected_value: Any,
    evidence: Dict[str, Any],
    exceptions: Optional[List[str]] = None,
    trigger: str = "on_event",
    scope: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Helper to create a standardized candidate from document extraction."""
    return {
        "doc_id": doc_id,
        "doc_class": doc_class,
        "effective_date": effective_date,
        "applies_to": applies_to,
        "type": rule_type,
        "basis": basis,
        "expected_value": expected_value,
        "evidence": evidence,
        "exceptions": exceptions or [],
        "trigger": trigger,
        "scope": scope or []
    }


def extract_candidates_from_ade_result(ade_result: Dict[str, Any], doc_id: str, doc_class: str) -> List[Dict[str, Any]]:
    """
    Extract rule candidates from LandingAI ADE result.
    
    This function processes the structured output from ADE and converts it to
    rule candidates that can be compiled into enforceable rules.
    """
    candidates = []
    
    # Process extracted fields for rule patterns
    fields = ade_result.get("fields", [])
    
    for field in fields:
        field_name = field.get("name", "").lower()
        field_value = field.get("value")
        evidence = {
            "doc": doc_id,
            "page": field.get("page_number", 1),
            "snippet": field.get("text_snippet", ""),
            "span_box": field.get("span_box")
        }
        
        # Map field patterns to rule types
        if "management_fee" in field_name or "fee_rate" in field_name:
            if isinstance(field_value, (int, float)):
                candidates.append(create_candidate_from_document(
                    doc_id=doc_id,
                    doc_class=doc_class,
                    effective_date=ade_result.get("effective_date", datetime.utcnow().isoformat()),
                    applies_to="ALL_INVESTORS",  # Default, can be overridden
                    rule_type="fee.rate_percent",
                    basis="management_fee",
                    expected_value=field_value,
                    evidence=evidence
                ))
        
        elif "reporting_deadline" in field_name or "reporting_requirement" in field_name:
            if isinstance(field_value, (int, float)):
                candidates.append(create_candidate_from_document(
                    doc_id=doc_id,
                    doc_class=doc_class,
                    effective_date=ade_result.get("effective_date", datetime.utcnow().isoformat()),
                    applies_to="ALL_INVESTORS",
                    rule_type="reporting.deadline_days",
                    basis="reporting_requirement",
                    expected_value=field_value,
                    evidence=evidence
                ))
        
        elif "prohibited_sector" in field_name or "allocation_restriction" in field_name:
            if isinstance(field_value, list):
                candidates.append(create_candidate_from_document(
                    doc_id=doc_id,
                    doc_class=doc_class,
                    effective_date=ade_result.get("effective_date", datetime.utcnow().isoformat()),
                    applies_to="ALL_INVESTORS",
                    rule_type="allocation.prohibited_sector",
                    basis="allocation",
                    expected_value=field_value,
                    evidence=evidence
                ))
    
    return candidates
