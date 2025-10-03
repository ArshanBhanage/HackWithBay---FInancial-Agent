"""Helper methods for LandingAI rule candidate extraction."""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_document_type(doc_id: str, document_type: str) -> str:
    """Classify document type from filename and content."""
    doc_id_lower = doc_id.lower()
    
    if "lpa" in doc_id_lower or "limited_partnership" in doc_id_lower:
        return "LPA"
    elif "side_letter" in doc_id_lower or "sideletter" in doc_id_lower:
        return "SideLetter"
    elif "amendment" in doc_id_lower:
        return "Amendment"
    elif "rider" in doc_id_lower:
        return "Rider"
    elif "credit" in doc_id_lower or "loan" in doc_id_lower:
        return "CreditAgreement"
    elif "policy" in doc_id_lower:
        return "Policy"
    elif "regulatory" in doc_id_lower or "filing" in doc_id_lower:
        return "RegulatoryFiling"
    else:
        return document_type or "LPA"  # Default fallback


def extract_parties(ade_result: Dict[str, Any], doc_class: str) -> Dict[str, List[str]]:
    """Extract parties from ADE result."""
    parties = {"gp": [], "fund": [], "investors": []}
    
    # Look for party information in extracted fields
    fields = ade_result.get("fields", [])
    for field in fields:
        field_name = field.get("name", "").lower()
        field_value = field.get("value", "")
        
        if "general_partner" in field_name or "gp" in field_name:
            if isinstance(field_value, list):
                parties["gp"].extend(field_value)
            else:
                parties["gp"].append(str(field_value))
        
        elif "fund_name" in field_name or "fund" in field_name:
            if isinstance(field_value, list):
                parties["fund"].extend(field_value)
            else:
                parties["fund"].append(str(field_value))
        
        elif "investor" in field_name or "limited_partner" in field_name:
            if isinstance(field_value, list):
                parties["investors"].extend(field_value)
            else:
                parties["investors"].append(str(field_value))
    
    return parties


def extract_effective_date(ade_result: Dict[str, Any], file_path: str) -> str:
    """Extract effective date from ADE result or file metadata."""
    # Look for effective date in extracted fields
    fields = ade_result.get("fields", [])
    for field in fields:
        field_name = field.get("name", "").lower()
        if "effective_date" in field_name or "date" in field_name:
            value = field.get("value")
            if value and isinstance(value, str):
                return value
    
    # Fallback to file modification date
    try:
        import os
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).isoformat()
    except:
        return datetime.utcnow().isoformat()


def extract_candidates_from_result(ade_result: Dict[str, Any], doc_id: str, doc_class: str, parties: Dict[str, List[str]], effective_date: str) -> List[Dict[str, Any]]:
    """Extract rule candidates from ADE result."""
    candidates = []
    
    # Determine applies_to based on document class
    if doc_class == "SideLetter":
        # Side letters apply to specific investors
        applies_to = parties["investors"] if parties["investors"] else ["ALL_INVESTORS"]
    else:
        # LPA, Amendment, Rider apply to all investors
        applies_to = "ALL_INVESTORS"
    
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
            if isinstance(field_value, (int, float)) and field_value > 0:
                candidates.append({
                    "doc_id": doc_id,
                    "doc_class": doc_class,
                    "effective_date": effective_date,
                    "applies_to": applies_to,
                    "type": "fee.rate_percent",
                    "basis": "management_fee",
                    "expected_value": field_value,
                    "evidence": evidence,
                    "exceptions": [],
                    "trigger": "fee_post"
                })
        
        elif "reporting_deadline" in field_name or "reporting_requirement" in field_name:
            if isinstance(field_value, (int, float)) and field_value > 0:
                candidates.append({
                    "doc_id": doc_id,
                    "doc_class": doc_class,
                    "effective_date": effective_date,
                    "applies_to": applies_to,
                    "type": "reporting.deadline_days",
                    "basis": "reporting_requirement",
                    "expected_value": field_value,
                    "evidence": evidence,
                    "exceptions": [],
                    "trigger": "quarter_end"
                })
        
        elif "prohibited_sector" in field_name or "allocation_restriction" in field_name:
            if isinstance(field_value, list) and field_value:
                candidates.append({
                    "doc_id": doc_id,
                    "doc_class": doc_class,
                    "effective_date": effective_date,
                    "applies_to": applies_to,
                    "type": "allocation.prohibited_sector",
                    "basis": "allocation",
                    "expected_value": field_value,
                    "evidence": evidence,
                    "exceptions": [],
                    "trigger": "trade_allocation"
                })
        
        elif "interest_rate" in field_name:
            if isinstance(field_value, (int, float)) and field_value > 0:
                candidates.append({
                    "doc_id": doc_id,
                    "doc_class": doc_class,
                    "effective_date": effective_date,
                    "applies_to": applies_to,
                    "type": "interest.rate_percent",
                    "basis": "interest_rate",
                    "expected_value": field_value,
                    "evidence": evidence,
                    "exceptions": [],
                    "trigger": "interest_calculation"
                })
    
    return candidates


async def extract_csv_rule_candidates(file_path: str, document_type: str) -> List[Dict[str, Any]]:
    """Extract rule candidates from CSV files."""
    logger.info(f"Extracting CSV rule candidates from: {file_path}")
    
    try:
        import pandas as pd
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        candidates = []
        doc_id = Path(file_path).name
        doc_class = "Policy"  # CSV files are typically policy data
        effective_date = datetime.utcnow().isoformat()
        
        # Look for fee-related columns
        for col in df.columns:
            col_lower = col.lower()
            if "fee" in col_lower and "rate" in col_lower:
                # Extract fee rates
                for idx, value in df[col].items():
                    if pd.notna(value) and isinstance(value, (int, float)) and value > 0:
                        candidates.append({
                            "doc_id": doc_id,
                            "doc_class": doc_class,
                            "effective_date": effective_date,
                            "applies_to": "ALL_INVESTORS",
                            "type": "fee.rate_percent",
                            "basis": "management_fee",
                            "expected_value": value,
                            "evidence": {
                                "doc": doc_id,
                                "page": 1,
                                "snippet": f"CSV row {idx}: {value}",
                                "span_box": None
                            },
                            "exceptions": [],
                            "trigger": "fee_post"
                        })
        
        return candidates
        
    except Exception as e:
        logger.error(f"Error extracting CSV rule candidates from {file_path}: {e}")
        return []


async def mock_rule_candidates(file_path: str, document_type: str) -> List[Dict[str, Any]]:
    """Mock rule candidates for testing when API key is not available."""
    logger.info(f"Mock rule candidates for {file_path}")
    
    doc_id = Path(file_path).name
    doc_class = classify_document_type(doc_id, document_type)
    effective_date = datetime.utcnow().isoformat()
    
    # Generate mock candidates based on document type
    mock_candidates = []
    
    if doc_class == "LPA":
        mock_candidates.extend([
            {
                "doc_id": doc_id,
                "doc_class": doc_class,
                "effective_date": effective_date,
                "applies_to": "ALL_INVESTORS",
                "type": "fee.rate_percent",
                "basis": "management_fee",
                "expected_value": 0.0175,  # 1.75%
                "evidence": {
                    "doc": doc_id,
                    "page": 1,
                    "snippet": "Management fee of 1.75%",
                    "span_box": None
                },
                "exceptions": [],
                "trigger": "fee_post"
            },
            {
                "doc_id": doc_id,
                "doc_class": doc_class,
                "effective_date": effective_date,
                "applies_to": "ALL_INVESTORS",
                "type": "reporting.deadline_days",
                "basis": "reporting_requirement",
                "expected_value": 5,
                "evidence": {
                    "doc": doc_id,
                    "page": 1,
                    "snippet": "Reports due within 5 business days",
                    "span_box": None
                },
                "exceptions": [],
                "trigger": "quarter_end"
            }
        ])
    
    elif doc_class == "SideLetter":
        mock_candidates.append({
            "doc_id": doc_id,
            "doc_class": doc_class,
            "effective_date": effective_date,
            "applies_to": ["Institution A"],  # Mock specific investor
            "type": "fee.rate_percent",
            "basis": "management_fee",
            "expected_value": 0.0150,  # 1.50% - better rate
            "evidence": {
                "doc": doc_id,
                "page": 1,
                "snippet": "Special management fee rate of 1.50%",
                "span_box": None
            },
            "exceptions": [],
            "trigger": "fee_post"
        })
    
    return mock_candidates
