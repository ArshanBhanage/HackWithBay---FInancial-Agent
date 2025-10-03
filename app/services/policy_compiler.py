"""Policy compiler for converting extracted contract data into enforceable rules."""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import yaml
import json

from ..models.contract import Contract, ContractVersion, ContractField
from ..models.obligation import Obligation, ObligationType, SeverityLevel, EnforcementAction, Evidence, EffectivePeriod
from ..models.policy import Policy, PolicyRule, ConflictCheck, PolicyStatus

logger = logging.getLogger(__name__)


class PolicyCompiler:
    """Service for compiling contract data into enforceable policy rules."""
    
    def __init__(self):
        self.field_mappings = self._initialize_field_mappings()
        self.rule_templates = self._initialize_rule_templates()
    
    def compile_policy(self, contracts: List[Contract], policy_id: str) -> Policy:
        """Compile a policy from multiple contracts."""
        logger.info(f"Compiling policy {policy_id} from {len(contracts)} contracts")
        
        # Create policy
        policy = Policy(
            policy_id=policy_id,
            generated_at=datetime.utcnow(),
            source_documents=self._extract_source_documents(contracts),
            ontology_version="o2a.v0.2"
        )
        
        try:
            # Extract entities
            entities = self._extract_entities(contracts)
            policy.entities = entities
            
            # Compile rules from each contract
            for contract in contracts:
                contract_rules = self._compile_contract_rules(contract)
                for rule in contract_rules:
                    policy.add_rule(rule)
            
            # Generate conflict checks
            conflict_checks = self._generate_conflict_checks(contracts)
            for check in conflict_checks:
                policy.add_conflict_check(check)
            
            # Validate policy
            issues = policy.validate_consistency()
            if issues:
                logger.warning(f"Policy validation issues: {issues}")
                policy.status = PolicyStatus.ERROR
            else:
                policy.status = PolicyStatus.COMPILED
                policy.compiled_at = datetime.utcnow()
            
            logger.info(f"Policy compilation completed: {len(policy.rules)} rules, {len(policy.conflict_checks)} conflict checks")
            return policy
            
        except Exception as e:
            logger.error(f"Error compiling policy: {e}")
            policy.status = PolicyStatus.ERROR
            return policy
    
    def _extract_source_documents(self, contracts: List[Contract]) -> List[Dict[str, str]]:
        """Extract source document information."""
        documents = []
        for contract in contracts:
            latest_version = contract.get_latest_version()
            if latest_version:
                documents.append({
                    "name": latest_version.document_path.split('/')[-1],
                    "hash": latest_version.document_hash
                })
        return documents
    
    def _extract_entities(self, contracts: List[Contract]) -> Dict[str, List[Dict[str, str]]]:
        """Extract entities (investors, beneficiaries) from contracts."""
        entities = {"investors": []}
        investor_ids = set()
        
        for contract in contracts:
            # Extract from contract metadata
            for beneficiary_id in contract.beneficiaries:
                if beneficiary_id not in investor_ids:
                    entities["investors"].append({
                        "id": beneficiary_id,
                        "legal_name": f"Entity {beneficiary_id}"  # Would be extracted from actual data
                    })
                    investor_ids.add(beneficiary_id)
            
            # Extract from contract fields
            latest_version = contract.get_latest_version()
            if latest_version:
                for field in latest_version.extracted_fields:
                    if "investor" in field.field_name.lower() or "beneficiary" in field.field_name.lower():
                        if field.value and field.value not in investor_ids:
                            entities["investors"].append({
                                "id": str(field.value),
                                "legal_name": str(field.value)
                            })
                            investor_ids.add(str(field.value))
        
        return entities
    
    def _compile_contract_rules(self, contract: Contract) -> List[PolicyRule]:
        """Compile rules from a single contract."""
        rules = []
        latest_version = contract.get_latest_version()
        
        if not latest_version:
            return rules
        
        # Group fields by type for rule generation
        field_groups = self._group_fields_by_type(latest_version.extracted_fields)
        
        # Generate rules for each field group
        for field_type, fields in field_groups.items():
            if field_type in self.field_mappings:
                rule_type = self.field_mappings[field_type]
                rule = self._create_rule_from_fields(rule_type, fields, contract, latest_version)
                if rule:
                    rules.append(rule)
        
        # Generate additional rules based on contract type
        additional_rules = self._generate_contract_specific_rules(contract, latest_version)
        rules.extend(additional_rules)
        
        return rules
    
    def _group_fields_by_type(self, fields: List[ContractField]) -> Dict[str, List[ContractField]]:
        """Group fields by their semantic type."""
        groups = {}
        
        for field in fields:
            field_name_lower = field.field_name.lower()
            
            # Categorize fields
            if any(keyword in field_name_lower for keyword in ["fee", "management_fee", "carried_interest"]):
                groups.setdefault("fee_rate", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["interest", "rate"]):
                groups.setdefault("interest_rate", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["deadline", "reporting", "notice"]):
                groups.setdefault("reporting_deadline", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["maturity", "expiry", "end_date"]):
                groups.setdefault("maturity_date", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["covenant", "requirement", "obligation"]):
                groups.setdefault("covenant", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["collateral", "security", "pledge"]):
                groups.setdefault("collateral", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["allocation", "restriction", "prohibited"]):
                groups.setdefault("allocation_restriction", []).append(field)
            elif any(keyword in field_name_lower for keyword in ["mfn", "most_favored", "favorable"]):
                groups.setdefault("mfn_notice", []).append(field)
            else:
                groups.setdefault("other", []).append(field)
        
        return groups
    
    def _create_rule_from_fields(self, rule_type: str, fields: List[ContractField], contract: Contract, version: ContractVersion) -> Optional[PolicyRule]:
        """Create a policy rule from grouped fields."""
        if not fields:
            return None
        
        # Use the first field as the primary field
        primary_field = fields[0]
        
        # Determine rule type
        obligation_type = self._map_to_obligation_type(rule_type)
        if not obligation_type:
            return None
        
        # Create rule
        rule = PolicyRule(
            id=f"{contract.contract_id}_{primary_field.field_name}_{rule_type}",
            type=obligation_type,
            applies_to=self._determine_applicable_entities(primary_field, contract),
            expected_value=primary_field.value,
            basis=self._determine_basis(primary_field),
            effective_period=self._determine_effective_period(contract, version),
            evidence=self._create_evidence(primary_field, version),
            severity=self._determine_severity(rule_type, primary_field),
            enforcement=self._determine_enforcement(rule_type)
        )
        
        return rule
    
    def _generate_contract_specific_rules(self, contract: Contract, version: ContractVersion) -> List[PolicyRule]:
        """Generate rules specific to contract type."""
        rules = []
        
        if contract.document_type.value == "side_letter":
            # Generate MFN notice rules
            mfn_rule = self._create_mfn_rule(contract, version)
            if mfn_rule:
                rules.append(mfn_rule)
        
        elif contract.document_type.value == "lpa":
            # Generate general fund rules
            fund_rules = self._create_fund_rules(contract, version)
            rules.extend(fund_rules)
        
        elif contract.document_type.value == "credit_agreement":
            # Generate credit-specific rules
            credit_rules = self._create_credit_rules(contract, version)
            rules.extend(credit_rules)
        
        return rules
    
    def _create_mfn_rule(self, contract: Contract, version: ContractVersion) -> Optional[PolicyRule]:
        """Create MFN notice rule for side letters."""
        # Look for MFN-related fields
        mfn_fields = [f for f in version.extracted_fields if "mfn" in f.field_name.lower()]
        
        if not mfn_fields:
            return None
        
        return PolicyRule(
            id=f"{contract.contract_id}_mfn_notice",
            type="mfn.notice_required",
            applies_to="ALL_INVESTORS",
            expected_value=10,  # Default threshold
            basis="mfn_threshold",
            effective_period={"start": version.uploaded_at.isoformat(), "end": None},
            evidence=self._create_evidence(mfn_fields[0], version),
            severity=SeverityLevel.MEDIUM,
            enforcement={"when": "on_sideletter_ingested", "action": "create_task"}
        )
    
    def _create_fund_rules(self, contract: Contract, version: ContractVersion) -> List[PolicyRule]:
        """Create general fund rules from LPA."""
        rules = []
        
        # Look for key fund terms
        key_fields = [f for f in version.extracted_fields if any(
            keyword in f.field_name.lower() for keyword in ["fund_size", "commitment", "investment_period"]
        )]
        
        for field in key_fields:
            rule = PolicyRule(
                id=f"{contract.contract_id}_{field.field_name}",
                type="covenant.requirement",
                applies_to="ALL_INVESTORS",
                expected_value=field.value,
                basis=field.field_name,
                effective_period={"start": version.uploaded_at.isoformat(), "end": None},
                evidence=self._create_evidence(field, version),
                severity=SeverityLevel.HIGH,
                enforcement={"when": "on_fund_operation", "action": "alert"}
            )
            rules.append(rule)
        
        return rules
    
    def _create_credit_rules(self, contract: Contract, version: ContractVersion) -> List[PolicyRule]:
        """Create credit-specific rules."""
        rules = []
        
        # Interest rate rules
        interest_fields = [f for f in version.extracted_fields if "interest" in f.field_name.lower()]
        for field in interest_fields:
            rule = PolicyRule(
                id=f"{contract.contract_id}_{field.field_name}",
                type="interest.rate_percent",
                applies_to="BORROWER",
                expected_value=field.value,
                basis="interest_rate",
                effective_period={"start": version.uploaded_at.isoformat(), "end": None},
                evidence=self._create_evidence(field, version),
                severity=SeverityLevel.HIGH,
                enforcement={"when": "on_interest_calculation", "action": "block_if_mismatch"}
            )
            rules.append(rule)
        
        return rules
    
    def _generate_conflict_checks(self, contracts: List[Contract]) -> List[ConflictCheck]:
        """Generate conflict checks between contracts."""
        checks = []
        
        # Check for fee rate conflicts between LPA and side letters
        lpa_contracts = [c for c in contracts if c.document_type.value == "lpa"]
        side_letter_contracts = [c for c in contracts if c.document_type.value == "side_letter"]
        
        if lpa_contracts and side_letter_contracts:
            check = ConflictCheck(
                id="FEE_RATE_CONFLICT_CHECK",
                description="Ensure side letter fee rates are within LPA bounds",
                compare={
                    "left": {
                        "source": "LPA",
                        "field": "mgmt_fee_range"
                    },
                    "right": {
                        "source": "SIDE_LETTER",
                        "field": "mgmt_fee_rate"
                    }
                },
                resolution="flag_if_outside_range"
            )
            checks.append(check)
        
        return checks
    
    def _initialize_field_mappings(self) -> Dict[str, str]:
        """Initialize mappings from field types to rule types."""
        return {
            "fee_rate": "fee.rate_percent",
            "interest_rate": "interest.rate_percent",
            "reporting_deadline": "reporting.deadline_days",
            "maturity_date": "maturity.date",
            "covenant": "covenant.requirement",
            "collateral": "collateral.requirement",
            "allocation_restriction": "allocation.prohibited_sector",
            "mfn_notice": "mfn.notice_required"
        }
    
    def _initialize_rule_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rule templates for different types."""
        return {
            "fee.rate_percent": {
                "severity": SeverityLevel.HIGH,
                "enforcement": {"when": "on_fee_calculation", "action": "block_if_mismatch"}
            },
            "interest.rate_percent": {
                "severity": SeverityLevel.HIGH,
                "enforcement": {"when": "on_interest_calculation", "action": "block_if_mismatch"}
            },
            "reporting.deadline_days": {
                "severity": SeverityLevel.MEDIUM,
                "enforcement": {"when": "on_report_generated", "action": "alert_if_missed"}
            },
            "maturity.date": {
                "severity": SeverityLevel.HIGH,
                "enforcement": {"when": "on_maturity_check", "action": "alert"}
            }
        }
    
    def _map_to_obligation_type(self, rule_type: str) -> Optional[str]:
        """Map rule type to obligation type."""
        return self.field_mappings.get(rule_type)
    
    def _determine_applicable_entities(self, field: ContractField, contract: Contract) -> Union[str, List[str]]:
        """Determine which entities this rule applies to."""
        # For now, apply to all investors
        # In a real implementation, this would be extracted from the contract
        return "ALL_INVESTORS"
    
    def _determine_basis(self, field: ContractField) -> Optional[str]:
        """Determine the basis for the rule."""
        field_name_lower = field.field_name.lower()
        
        if "management" in field_name_lower:
            return "management_fee"
        elif "interest" in field_name_lower:
            return "interest_rate"
        elif "reporting" in field_name_lower:
            return "reporting_requirement"
        else:
            return field.field_name
    
    def _determine_effective_period(self, contract: Contract, version: ContractVersion) -> Dict[str, Any]:
        """Determine the effective period for the rule."""
        return {
            "start": version.uploaded_at.isoformat(),
            "end": None  # Would be extracted from contract terms
        }
    
    def _create_evidence(self, field: ContractField, version: ContractVersion) -> Dict[str, Any]:
        """Create evidence for the rule."""
        return {
            "doc": version.document_path.split('/')[-1],
            "page": field.page_number,
            "text_snippet": field.text_snippet,
            "table_cell": field.table_cell
        }
    
    def _determine_severity(self, rule_type: str, field: ContractField) -> SeverityLevel:
        """Determine severity level for the rule."""
        template = self.rule_templates.get(rule_type, {})
        return template.get("severity", SeverityLevel.MEDIUM)
    
    def _determine_enforcement(self, rule_type: str) -> Dict[str, Any]:
        """Determine enforcement action for the rule."""
        template = self.rule_templates.get(rule_type, {})
        return template.get("enforcement", {"when": "on_event", "action": "alert"})
    
    def export_policy_yaml(self, policy: Policy, file_path: str) -> None:
        """Export policy to YAML file."""
        yaml_content = policy.to_yaml()
        with open(file_path, 'w') as f:
            f.write(yaml_content)
        logger.info(f"Policy exported to {file_path}")
    
    def export_policy_json(self, policy: Policy, file_path: str) -> None:
        """Export policy to JSON file."""
        policy_dict = policy.dict()
        with open(file_path, 'w') as f:
            json.dump(policy_dict, f, indent=2, default=str)
        logger.info(f"Policy exported to {file_path}")
