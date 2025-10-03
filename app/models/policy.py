"""Policy and rule models for contract enforcement."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .obligation import Obligation, SeverityLevel, EnforcementAction


class PolicyStatus(str, Enum):
    """Status of policy compilation and deployment."""
    DRAFT = "draft"
    COMPILED = "compiled"
    DEPLOYED = "deployed"
    ERROR = "error"


class RuleType(str, Enum):
    """Types of policy rules."""
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


class PolicyRule(BaseModel):
    """A single rule within a policy pack."""
    id: str
    type: RuleType
    applies_to: Union[str, List[str]]
    expected_value: Any
    basis: Optional[str] = None
    
    # Temporal validity
    effective_period: Dict[str, Any]  # start/end dates
    
    # Evidence
    evidence: Dict[str, Any]  # document, page, text_snippet
    
    # Risk and enforcement
    severity: SeverityLevel
    enforcement: Dict[str, Any]  # when/action
    
    # Optional fields
    exceptions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConflictCheck(BaseModel):
    """Configuration for checking conflicts between documents."""
    id: str
    description: str
    compare: Dict[str, Any]  # left/right sources
    resolution: str  # action to take on conflict


class Policy(BaseModel):
    """Policy pack containing rules and conflict checks."""
    policy_id: str
    generated_at: datetime
    source_documents: List[Dict[str, str]]  # name/hash pairs
    ontology_version: str = "o2a.v0.2"
    
    # Entities
    entities: Dict[str, List[Dict[str, str]]] = {}  # investors, etc.
    
    # Rules and checks
    rules: List[PolicyRule] = []
    conflict_checks: List[ConflictCheck] = []
    
    # Status
    status: PolicyStatus = PolicyStatus.DRAFT
    compiled_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_rule(self, rule: PolicyRule) -> None:
        """Add a rule to this policy."""
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()
    
    def add_conflict_check(self, check: ConflictCheck) -> None:
        """Add a conflict check to this policy."""
        self.conflict_checks.append(check)
        self.updated_at = datetime.utcnow()
    
    def get_rules_for_entity(self, entity_id: str) -> List[PolicyRule]:
        """Get all rules that apply to a specific entity."""
        applicable_rules = []
        for rule in self.rules:
            if isinstance(rule.applies_to, str):
                if rule.applies_to == entity_id or rule.applies_to == "ALL_INVESTORS":
                    applicable_rules.append(rule)
            elif entity_id in rule.applies_to:
                applicable_rules.append(rule)
        return applicable_rules
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[PolicyRule]:
        """Get all rules of a specific type."""
        return [rule for rule in self.rules if rule.type == rule_type]
    
    def validate_consistency(self) -> List[str]:
        """Validate policy consistency and return any issues."""
        issues = []
        
        # Check for duplicate rule IDs
        rule_ids = [rule.id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            issues.append("Duplicate rule IDs found")
        
        # Check for duplicate conflict check IDs
        check_ids = [check.id for check in self.conflict_checks]
        if len(check_ids) != len(set(check_ids)):
            issues.append("Duplicate conflict check IDs found")
        
        # Validate rule references in conflict checks
        for check in self.conflict_checks:
            if "source_rule" in check.compare.get("right", {}):
                rule_id = check.compare["right"]["source_rule"]
                if not any(rule.id == rule_id for rule in self.rules):
                    issues.append(f"Conflict check {check.id} references non-existent rule {rule_id}")
        
        return issues
    
    def to_yaml(self) -> str:
        """Convert policy to YAML format."""
        import yaml
        
        policy_dict = {
            "policy_id": self.policy_id,
            "generated_at": self.generated_at.isoformat(),
            "source_documents": self.source_documents,
            "ontology_version": self.ontology_version,
            "entities": self.entities,
            "rules": [rule.dict() for rule in self.rules],
            "conflict_checks": [check.dict() for check in self.conflict_checks]
        }
        
        return yaml.dump(policy_dict, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> "Policy":
        """Create policy from YAML content."""
        import yaml
        
        data = yaml.safe_load(yaml_content)
        
        # Convert rules
        rules = [PolicyRule(**rule_data) for rule_data in data.get("rules", [])]
        
        # Convert conflict checks
        conflict_checks = [ConflictCheck(**check_data) for check_data in data.get("conflict_checks", [])]
        
        return cls(
            policy_id=data["policy_id"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            source_documents=data["source_documents"],
            ontology_version=data.get("ontology_version", "o2a.v0.2"),
            entities=data.get("entities", {}),
            rules=rules,
            conflict_checks=conflict_checks
        )
