"""AI-powered rule extraction agent using Claude for intelligent document analysis."""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import httpx
from anthropic import Anthropic

from ..config import settings
from ..models.policy import PolicyRule, RuleType
from ..models.obligation import SeverityLevel

logger = logging.getLogger(__name__)


class AIRuleAgent:
    """AI agent for intelligent rule extraction and policy compilation using Claude."""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.model = "claude-3-5-haiku-20241022"
        
        if self.client:
            logger.info("AI Rule Agent initialized with Claude")
        else:
            logger.warning("Anthropic API key not found, using mock AI agent")
    
    async def create_rules_from_landingai_data(self, landingai_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create rules from LandingAI extracted data using Claude AI."""
        logger.info(f"AI agent creating rules from LandingAI data: {landingai_data['document_id']}")
        
        if not self.client:
            raise ValueError("Claude API key required for rule creation")
        
        try:
            # Create AI prompt for rule creation from structured data
            prompt = self._create_rule_creation_prompt(landingai_data)
            
            # Call Claude API
            response = await self._call_claude(prompt)
            
            # Parse AI response into rule candidates
            candidates = self._parse_ai_response(response, landingai_data['document_id'], landingai_data['document_class'])
            
            logger.info(f"AI agent created {len(candidates)} rules from LandingAI data")
            return candidates
            
        except Exception as e:
            logger.error(f"Error in AI rule creation from LandingAI data: {e}")
            raise
    
    async def compile_policies_intelligently(self, candidates: List[Dict[str, Any]]) -> List[PolicyRule]:
        """Use AI to intelligently compile policies with conflict resolution."""
        logger.info(f"AI agent compiling {len(candidates)} candidates into policies")
        
        if not self.client:
            return self._basic_rule_compilation(candidates)
        
        try:
            # Create AI prompt for policy compilation
            prompt = self._create_policy_compilation_prompt(candidates)
            
            # Call Claude API
            response = await self._call_claude(prompt)
            
            # Parse AI response into compiled policies
            policies = self._parse_policy_compilation_response(response, candidates)
            
            logger.info(f"AI agent compiled {len(policies)} policies from {len(candidates)} candidates")
            return policies
            
        except Exception as e:
            logger.error(f"Error in AI policy compilation: {e}")
            return self._basic_rule_compilation(candidates)
    
    async def analyze_compliance_violations(self, operational_data: Dict[str, Any], policies: List[PolicyRule]) -> List[Dict[str, Any]]:
        """Use AI to analyze potential compliance violations."""
        logger.info("AI agent analyzing compliance violations")
        
        if not self.client:
            return self._mock_violation_analysis(operational_data, policies)
        
        try:
            # Create AI prompt for violation analysis
            prompt = self._create_violation_analysis_prompt(operational_data, policies)
            
            # Call Claude API
            response = await self._call_claude(prompt)
            
            # Parse AI response into violation alerts
            violations = self._parse_violation_analysis_response(response, operational_data, policies)
            
            logger.info(f"AI agent identified {len(violations)} potential violations")
            return violations
            
        except Exception as e:
            logger.error(f"Error in AI violation analysis: {e}")
            return self._mock_violation_analysis(operational_data, policies)
    
    async def prioritize_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to intelligently prioritize alerts."""
        logger.info(f"AI agent prioritizing {len(alerts)} alerts")
        
        if not self.client:
            return alerts  # Return as-is if no AI
        
        try:
            # Create AI prompt for alert prioritization
            prompt = self._create_alert_prioritization_prompt(alerts)
            
            # Call Claude API
            response = await self._call_claude(prompt)
            
            # Parse AI response and reorder alerts
            prioritized_alerts = self._parse_alert_prioritization_response(response, alerts)
            
            logger.info(f"AI agent prioritized {len(prioritized_alerts)} alerts")
            return prioritized_alerts
            
        except Exception as e:
            logger.error(f"Error in AI alert prioritization: {e}")
            return alerts
    
    def _create_rule_creation_prompt(self, landingai_data: Dict[str, Any]) -> str:
        """Create AI prompt for rule creation from LandingAI structured data."""
        doc_id = landingai_data['document_id']
        doc_class = landingai_data['document_class']
        fields = landingai_data.get('extracted_fields', [])
        chunks = landingai_data.get('chunks', [])
        raw_content = landingai_data.get('raw_content', '')
        parties = landingai_data.get('parties', {})
        effective_date = landingai_data.get('effective_date', '')
        
        # Format extracted fields for AI analysis
        fields_text = ""
        for field in fields:
            fields_text += f"- {field.get('name', 'Unknown')}: {field.get('value', 'N/A')} (Page {field.get('page_number', 'N/A')})\n"
        
        # Format chunks for AI analysis
        chunks_text = ""
        for chunk in chunks:
            chunks_text += f"- {chunk.get('type', 'text')}: {chunk.get('content', '')[:200]}...\n"
        
        return f"""You are an expert financial contract analyst. Analyze the following document data extracted by LandingAI ADE and create enforceable rules.

Document: {doc_id}
Type: {doc_class}
Effective Date: {effective_date}
Parties: {parties}

LandingAI Extracted Fields:
{fields_text}

Document Chunks:
{chunks_text}

Raw Document Content (first 2000 chars):
{raw_content[:2000]}

Create enforceable rules in this EXACT JSON format:
[
  {{
    "rule_id": "unique_rule_id",
    "type": "fee.rate_percent|reporting.deadline_days|allocation.prohibited_sector|interest.rate_percent|mfn.threshold_bps|mfn.notice_deadline_days|covenant.requirement",
    "basis": "management_fee|reporting_requirement|allocation|interest_rate|mfn|covenant",
    "expected_value": "decimal_value_for_rates_or_numeric_value",
    "applies_to": "ALL_INVESTORS_or_specific_investor_list",
    "effective_date": "{effective_date}",
    "exceptions": [],
    "enforcement": {{
      "when": "on_fee_calculation_post|on_report_generated|on_sideletter_ingested|on_interest_post|on_trade_allocation",
      "action": "block_if_mismatch|alert_if_missed|alert_if_mismatch|create_task"
    }},
    "severity": "HIGH|MEDIUM|LOW",
    "evidence": {{
      "doc": "{doc_id}",
      "page": 1,
      "text_snippet": "relevant_text_excerpt_from_landingai_extraction"
    }},
    "description": "human_readable_rule_description"
  }}
]

CRITICAL FORMATTING RULES:
- For percentage rates (fee.rate_percent, interest.rate_percent): convert to decimal (1.75% → 0.0175)
- For MFN threshold: use mfn.threshold_bps type with basis points value
- For MFN notice: use mfn.notice_deadline_days type with days value
- enforcement must be an object with "when" and "action" fields, not a string
- basis must match ValidationEngine field mappings: management_fee, reporting_requirement, interest_rate, mfn

Focus on extracting rules from the LandingAI structured data. Use the extracted fields as the primary source, with chunks and raw content as supporting context.

Return ONLY the JSON array, no other text."""
    
    def _create_rule_extraction_prompt(self, file_path: str, document_type: str, content: str) -> str:
        """Create AI prompt for rule extraction."""
        return f"""You are an expert financial contract analyst. Analyze the following {document_type} document and extract all enforceable rules and obligations.

Document: {Path(file_path).name}
Type: {document_type}
Content: {content[:8000]}  # Truncate for token limits

Extract rules in this EXACT JSON format:
[
  {{
    "rule_id": "unique_id",
    "type": "fee.rate_percent|reporting.deadline_days|allocation.prohibited_sector|interest.rate_percent|mfn.notice_required|covenant.requirement",
    "basis": "management_fee|reporting_requirement|allocation|interest_rate|mfn_clause|covenant",
    "expected_value": "numeric_value_or_array",
    "applies_to": "ALL_INVESTORS_or_specific_investor_list",
    "effective_date": "YYYY-MM-DD",
    "exceptions": ["exception1", "exception2"],
    "trigger": "fee_post|quarter_end|trade_allocation|interest_calculation|mfn_trigger|covenant_check",
    "severity": "HIGH|MEDIUM|LOW",
    "evidence": {{
      "doc": "document_name",
      "page": 1,
      "snippet": "relevant_text_excerpt"
    }},
    "description": "human_readable_rule_description"
  }}
]

Focus on:
1. Management fees and performance fees
2. Reporting deadlines and requirements  
3. Investment restrictions and allocations
4. Interest rates and payment terms
5. Most Favored Nation (MFN) clauses
6. Covenants and compliance requirements

Return ONLY the JSON array, no other text."""
    
    def _create_policy_compilation_prompt(self, candidates: List[Dict[str, Any]]) -> str:
        """Create AI prompt for policy compilation."""
        return f"""You are an expert policy compiler. Analyze these rule candidates and compile them into enforceable policies with conflict resolution.

Rule Candidates: {json.dumps(candidates, indent=2)}

Apply these precedence rules:
1. Amendment/Rider > Side Letter > LPA/Credit Agreement
2. Later effective date > earlier effective date
3. Specific investor > ALL_INVESTORS for same investor
4. More restrictive > less restrictive

Return compiled policies in this EXACT JSON format:
[
  {{
    "rule_id": "compiled_rule_id",
    "type": "rule_type",
    "basis": "rule_basis", 
    "expected_value": "final_value",
    "applies_to": "target_scope",
    "effective_period": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD_or_null"}},
    "severity": "HIGH|MEDIUM|LOW",
    "evidence": {{"doc": "doc_name", "page": 1, "snippet": "text"}},
    "exceptions": ["exception_list"],
    "trigger": "trigger_condition",
    "description": "compiled_rule_description",
    "conflicts": ["list_of_resolved_conflicts"],
    "history": ["list_of_superseded_rules"]
  }}
]

Resolve conflicts intelligently and provide clear reasoning. Return ONLY the JSON array."""
    
    def _create_violation_analysis_prompt(self, operational_data: Dict[str, Any], policies: List[PolicyRule]) -> str:
        """Create AI prompt for violation analysis."""
        policies_json = [policy.model_dump() for policy in policies]
        
        return f"""You are an expert compliance analyst. Analyze operational data against policies to identify violations.

Operational Data: {json.dumps(operational_data, indent=2)}
Policies: {json.dumps(policies_json, indent=2)}

Check each policy against the operational data and identify violations. Return results in this EXACT JSON format:
[
  {{
    "alert_id": "unique_alert_id",
    "type": "rule_violation",
    "severity": "HIGH|MEDIUM|LOW",
    "title": "Violation: Rule Name",
    "description": "detailed_violation_description",
    "rule_id": "violated_rule_id",
    "expected_value": "expected_value",
    "actual_value": "actual_value_from_data",
    "entity_id": "affected_entity",
    "investor_name": "affected_investor",
    "evidence_doc": "source_document",
    "evidence_page": 1,
    "evidence_snippet": "relevant_text",
    "status": "new",
    "created_at": "YYYY-MM-DDTHH:MM:SSZ",
    "risk_assessment": "high_medium_low_risk_explanation",
    "recommended_action": "specific_remediation_steps"
  }}
]

Be thorough but precise. Only flag actual violations. Return ONLY the JSON array."""
    
    def _create_alert_prioritization_prompt(self, alerts: List[Dict[str, Any]]) -> str:
        """Create AI prompt for alert prioritization."""
        return f"""You are an expert risk manager. Prioritize these compliance alerts by urgency and business impact.

Alerts: {json.dumps(alerts, indent=2)}

Consider:
1. Financial impact (fees, penalties, losses)
2. Regulatory risk (compliance violations, reporting failures)
3. Operational risk (process failures, system issues)
4. Reputational risk (client relationships, market perception)
5. Time sensitivity (deadlines, expiration dates)

Return prioritized alerts in this EXACT JSON format:
[
  {{
    "alert_id": "original_alert_id",
    "priority_score": 1-10,
    "priority_reason": "explanation_of_priority",
    "urgency": "CRITICAL|HIGH|MEDIUM|LOW",
    "business_impact": "HIGH|MEDIUM|LOW",
    "recommended_timeline": "immediate|within_24h|within_week|within_month",
    "escalation_required": true/false,
    "stakeholders": ["list_of_notify_stakeholders"]
  }}
]

Sort by priority_score descending. Return ONLY the JSON array."""
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=4000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _read_file_content(self, file_path: str) -> str:
        """Read file content for AI analysis."""
        try:
            if file_path.lower().endswith('.pdf'):
                # For PDFs, we'd need to extract text first
                # For now, return a placeholder
                return f"PDF document: {Path(file_path).name}"
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"
    
    def _parse_ai_response(self, response: str, file_path: str, document_type: str) -> List[Dict[str, Any]]:
        """Parse AI response into rule candidates."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            candidates = json.loads(json_str)
            
            # Add document metadata
            doc_id = Path(file_path).name
            for candidate in candidates:
                candidate['doc_id'] = doc_id
                candidate['doc_class'] = document_type
                candidate['evidence']['doc'] = doc_id
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return []
    
    def _parse_policy_compilation_response(self, response: str, original_candidates: List[Dict[str, Any]]) -> List[PolicyRule]:
        """Parse AI policy compilation response into PolicyRule objects."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            compiled_data = json.loads(json_str)
            
            # Convert to PolicyRule objects
            policies = []
            for rule_data in compiled_data:
                try:
                    policy = PolicyRule(
                        id=rule_data.get('rule_id', f"rule_{len(policies)}"),
                        type=RuleType(rule_data['type']),
                        applies_to=rule_data['applies_to'] if isinstance(rule_data['applies_to'], list) else [rule_data['applies_to']],
                        expected_value=rule_data['expected_value'],
                        basis=rule_data['basis'],
                        effective_period=rule_data.get('effective_period', {'start': datetime.utcnow().isoformat(), 'end': None}),
                        evidence=rule_data.get('evidence', {}),
                        severity=SeverityLevel(rule_data.get('severity', 'LOW')),
                        enforcement={'when': rule_data.get('trigger', 'on_event'), 'action': 'alert'},
                        exceptions=rule_data.get('exceptions', []),
                        metadata={
                            'compiled_at': datetime.utcnow().isoformat(),
                            'conflicts': rule_data.get('conflicts', []),
                            'history': rule_data.get('history', []),
                            'ai_compiled': True
                        }
                    )
                    policies.append(policy)
                except Exception as e:
                    logger.error(f"Error creating PolicyRule from {rule_data}: {e}")
            
            return policies
            
        except Exception as e:
            logger.error(f"Error parsing policy compilation response: {e}")
            return []
    
    def _parse_violation_analysis_response(self, response: str, operational_data: Dict[str, Any], policies: List[PolicyRule]) -> List[Dict[str, Any]]:
        """Parse AI violation analysis response into alert objects."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            violations = json.loads(json_str)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error parsing violation analysis response: {e}")
            return []
    
    def _parse_alert_prioritization_response(self, response: str, original_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse AI alert prioritization response and apply to original alerts."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            prioritization = json.loads(json_str)
            
            # Create mapping from alert_id to priority info
            priority_map = {item['alert_id']: item for item in prioritization}
            
            # Apply prioritization to original alerts
            prioritized_alerts = []
            for alert in original_alerts:
                alert_id = alert.get('alert_id', alert.get('id'))
                if alert_id in priority_map:
                    priority_info = priority_map[alert_id]
                    alert.update({
                        'priority_score': priority_info.get('priority_score', 5),
                        'priority_reason': priority_info.get('priority_reason', ''),
                        'urgency': priority_info.get('urgency', 'MEDIUM'),
                        'business_impact': priority_info.get('business_impact', 'MEDIUM'),
                        'recommended_timeline': priority_info.get('recommended_timeline', 'within_week'),
                        'escalation_required': priority_info.get('escalation_required', False),
                        'stakeholders': priority_info.get('stakeholders', [])
                    })
                prioritized_alerts.append(alert)
            
            # Sort by priority score
            prioritized_alerts.sort(key=lambda x: x.get('priority_score', 5), reverse=True)
            
            return prioritized_alerts
            
        except Exception as e:
            logger.error(f"Error parsing alert prioritization response: {e}")
            return original_alerts
    
    def _basic_rule_compilation(self, candidates: List[Dict[str, Any]]) -> List[PolicyRule]:
        """Fallback basic rule compilation without AI."""
        from .rule_compiler import RuleCompiler
        compiler = RuleCompiler()
        return compiler.compile_rules(candidates)
    
    
