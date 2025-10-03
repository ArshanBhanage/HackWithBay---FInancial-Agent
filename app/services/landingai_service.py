"""LandingAI service for document extraction using ADE DPT-2."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import base64
from pathlib import Path
import os

import httpx
from dotenv import load_dotenv

from ..config import settings
from ..models.contract import ContractField, ContractVersion, ContractStatus
from .landingai_rule_helpers import (
    classify_document_type, extract_parties, extract_effective_date,
    extract_candidates_from_result, extract_csv_rule_candidates, mock_rule_candidates
)

logger = logging.getLogger(__name__)


class LandingAIService:
    """Service for document extraction using LandingAI ADE DPT-2."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LANDINGAI_API_KEY")
        self.base_url = "https://api.va.landing.ai/v1/ade/parse"
        self.model = "dpt-2-latest"
        
        if self.api_key:
            logger.info("LandingAI ADE service initialized successfully")
        else:
            logger.warning("LandingAI API key not found, using mock extraction")
    
    async def extract_document(self, file_path: str, document_type: str) -> List[ContractField]:
        """Extract structured fields from a document."""
        logger.info(f"Extracting document: {file_path}")
        
        # Check if file is CSV - handle differently
        if file_path.lower().endswith('.csv'):
            return await self._extract_csv_data(file_path, document_type)
        
        if not self.api_key:
            return await self._mock_extraction(file_path, document_type)
        
        try:
            # Extract using LandingAI ADE DPT-2 API (PDFs only)
            result = await self._extract_with_retry(file_path)
            
            # Convert to ContractField objects
            fields = self._convert_to_contract_fields(result, file_path)
            
            logger.info(f"Extracted {len(fields)} fields from {file_path}")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting document {file_path}: {e}")
            return []
    
    async def extract_document_for_ai(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract structured document data for AI rule processing."""
        logger.info(f"Extracting document data for AI processing: {file_path}")
        
        if not self.api_key:
            raise ValueError("LandingAI API key required for document extraction")
        
        try:
            # Extract using LandingAI ADE DPT-2 API
            result = await self._extract_with_retry(file_path)
            
            # Extract document metadata
            doc_id = Path(file_path).name
            doc_class = classify_document_type(doc_id, document_type)
            parties = extract_parties(result, doc_class)
            effective_date = extract_effective_date(result, file_path)
            
            # Structure the data for Claude processing
            structured_data = {
                "document_id": doc_id,
                "document_class": doc_class,
                "document_type": document_type,
                "effective_date": effective_date,
                "parties": parties,
                "extracted_fields": result.get("fields", []),
                "chunks": result.get("chunks", []),
                "splits": result.get("splits", []),
                "tables": result.get("tables", []),
                "raw_content": result.get("markdown", result.get("text", "")),
                "metadata": {
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "file_path": file_path,
                    "extraction_method": "landingai_ade_dpt2"
                }
            }
            
            logger.info(f"Extracted structured data from {doc_id} with {len(structured_data['extracted_fields'])} fields")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting document data from {file_path}: {e}")
            raise
    
    async def extract_table_data(self, file_path: str, table_config: Dict[str, Any]) -> List[ContractField]:
        """Extract structured data from tables within documents."""
        logger.info(f"Extracting table data from: {file_path}")
        
        if not self.extractor:
            return await self._mock_table_extraction(file_path, table_config)
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Use table-specific extraction
            result = await self._extract_table_with_retry(file_content, table_config)
            
            # Convert to ContractField objects
            fields = self._convert_table_to_contract_fields(result, file_path, table_config)
            
            logger.info(f"Extracted {len(fields)} table fields from {file_path}")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting table data from {file_path}: {e}")
            return []
    
    async def extract_parallel_fields(self, file_path: str, field_definitions: List[Dict[str, Any]]) -> List[ContractField]:
        """Extract multiple fields in parallel for better performance."""
        logger.info(f"Extracting parallel fields from: {file_path}")
        
        if not self.extractor:
            return await self._mock_parallel_extraction(file_path, field_definitions)
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create extraction tasks for parallel processing
            tasks = []
            for field_def in field_definitions:
                task = self._extract_single_field(file_content, field_def)
                tasks.append(task)
            
            # Execute in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            all_fields = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error extracting field {field_definitions[i]['name']}: {result}")
                else:
                    all_fields.extend(result)
            
            logger.info(f"Extracted {len(all_fields)} fields in parallel from {file_path}")
            return all_fields
            
        except Exception as e:
            logger.error(f"Error in parallel extraction from {file_path}: {e}")
            return []
    
    async def _extract_csv_data(self, file_path: str, document_type: str) -> List[ContractField]:
        """Extract data from CSV files."""
        logger.info(f"Extracting CSV data from: {file_path}")
        
        try:
            import pandas as pd
            
            # Read CSV file
            df = pd.read_csv(file_path)
            fields = []
            
            # Extract each row as a field
            for idx, row in df.iterrows():
                for col_name, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        field = ContractField(
                            field_name=f"{col_name}_{idx}",
                            field_type="csv_cell",
                            value=str(value),
                            confidence=1.0,
                            page_number=1,
                            text_snippet=str(value),
                            table_cell=f"R{idx}C{list(df.columns).index(col_name)}",
                            bounding_box=None
                        )
                        fields.append(field)
            
            logger.info(f"Extracted {len(fields)} fields from CSV {file_path}")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting CSV data from {file_path}: {e}")
            return []
            
        except Exception as e:
            logger.error(f"Error in parallel extraction from {file_path}: {e}")
            return []
    
    async def _extract_with_retry(self, file_path: str, max_retries: int = 3) -> Dict[str, Any]:
        """Extract document with retry logic using ADE API."""
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    with open(file_path, 'rb') as f:
                        files = {'document': f}
                        data = {'model': self.model}
                        headers = {'Authorization': f'Bearer {self.api_key}'}
                        
                        response = await client.post(
                            self.base_url,
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=60.0
                        )
                        
                        response.raise_for_status()
                        result = response.json()
                        
                        logger.info(f"ADE API response received for {file_path}")
                        return result
                        
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Extraction attempt {attempt + 1} failed: {e}. Retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {}
    
    async def _extract_table_with_retry(self, file_content: bytes, table_config: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Extract table data with retry logic."""
        for attempt in range(max_retries):
            try:
                # Use table-specific extraction method
                result = await asyncio.to_thread(
                    self.extractor.predict,
                    file_content
                )
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Table extraction attempt {attempt + 1} failed: {e}. Retrying...")
                await asyncio.sleep(2 ** attempt)
        
        return {}
    
    async def _extract_single_field(self, file_content: bytes, field_definition: Dict[str, Any]) -> List[ContractField]:
        """Extract a single field from document."""
        try:
            result = await asyncio.to_thread(
                self.extractor.predict,
                file_content
            )
            return self._convert_single_field_to_contract_field(result, field_definition)
        except Exception as e:
            logger.error(f"Error extracting field {field_definition.get('name', 'unknown')}: {e}")
            return []
    
    def _map_document_type(self, document_type: str) -> str:
        """Map internal document type to LandingAI document type."""
        mapping = {
            "lpa": "financial_contract",
            "side_letter": "financial_contract", 
            "subscription_agreement": "financial_contract",
            "credit_agreement": "financial_contract",
            "insurance_policy": "insurance_policy",
            "amendment": "legal_document",
            "rider": "legal_document",
            "regulatory_filing": "regulatory_document",
            "other": "general_document"
        }
        return mapping.get(document_type.lower(), "general_document")
    
    def _convert_to_contract_fields(self, extraction_result: Dict[str, Any], file_path: str) -> List[ContractField]:
        """Convert LandingAI ADE result to ContractField objects."""
        fields = []
        
        if not extraction_result:
            return fields
        
        # Process chunks from ADE response
        chunks = extraction_result.get("chunks", [])
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("id", f"chunk_{i}")
            chunk_type = chunk.get("type", "text")
            markdown = chunk.get("markdown", "")
            grounding = chunk.get("grounding", {})
            
            # Extract bounding box and page info
            box = grounding.get("box", {})
            page_number = grounding.get("page", 1)
            
            field = ContractField(
                field_name=chunk_id,
                field_type=chunk_type,
                value=markdown,
                confidence=0.9,  # ADE doesn't provide confidence scores
                page_number=page_number,
                text_snippet=markdown,
                table_cell=None,
                bounding_box={
                    "left": box.get("left"),
                    "top": box.get("top"),
                    "right": box.get("right"),
                    "bottom": box.get("bottom")
                } if box else None
            )
            fields.append(field)
        
        # Process splits from ADE response
        splits = extraction_result.get("splits", [])
        for i, split in enumerate(splits):
            split_class = split.get("class", f"split_{i}")
            identifier = split.get("identifier", f"split_{i}")
            pages = split.get("pages", [1])
            markdown = split.get("markdown", "")
            
            field = ContractField(
                field_name=f"{split_class}_{identifier}",
                field_type="split",
                value=markdown,
                confidence=0.9,
                page_number=pages[0] if pages else 1,
                text_snippet=markdown,
                table_cell=None,
                bounding_box=None
            )
            fields.append(field)
        
        return fields
    
    def _convert_table_to_contract_fields(self, table_result: Dict[str, Any], file_path: str, table_config: Dict[str, Any]) -> List[ContractField]:
        """Convert table extraction result to ContractField objects."""
        fields = []
        
        if not table_result or "tables" not in table_result:
            return fields
        
        for table_data in table_result["tables"]:
            table_name = table_data.get("name", "unknown_table")
            rows = table_data.get("rows", [])
            
            for row_idx, row in enumerate(rows):
                for col_idx, cell_value in enumerate(row):
                    if cell_value and str(cell_value).strip():
                        field = ContractField(
                            field_name=f"{table_name}_row_{row_idx}_col_{col_idx}",
                            field_type="table_cell",
                            value=cell_value,
                            confidence=table_data.get("confidence", 0.0),
                            page_number=table_data.get("page_number", 1),
                            text_snippet=str(cell_value),
                            table_cell=f"R{row_idx}C{col_idx}",
                            bounding_box=table_data.get("bounding_box")
                        )
                        fields.append(field)
        
        return fields
    
    def _convert_single_field_to_contract_field(self, field_result: Dict[str, Any], field_definition: Dict[str, Any]) -> List[ContractField]:
        """Convert single field extraction result to ContractField."""
        if not field_result:
            return []
        
        field = ContractField(
            field_name=field_definition.get("name", "unknown"),
            field_type=field_definition.get("type", "string"),
            value=field_result.get("value"),
            confidence=field_result.get("confidence", 0.0),
            page_number=field_result.get("page_number", 1),
            text_snippet=field_result.get("text_snippet", ""),
            table_cell=field_result.get("table_cell"),
            bounding_box=field_result.get("bounding_box")
        )
        
        return [field]
    
    async def _mock_extraction(self, file_path: str, document_type: str) -> List[ContractField]:
        """Mock extraction for testing when API key is not available."""
        logger.info(f"Mock extraction for {file_path}")
        
        # Generate mock fields based on document type
        mock_fields = []
        
        if document_type in ["lpa", "side_letter"]:
            mock_fields = [
                ContractField(
                    field_name="management_fee_rate",
                    field_type="percentage",
                    value=1.75,
                    confidence=0.95,
                    page_number=7,
                    text_snippet="Management fee shall be one point seven five percent (1.75%)",
                    table_cell=None
                ),
                ContractField(
                    field_name="reporting_deadline_days",
                    field_type="integer",
                    value=5,
                    confidence=0.90,
                    page_number=3,
                    text_snippet="Quarterly reports shall be delivered within five (5) business days",
                    table_cell=None
                )
            ]
        elif document_type == "credit_agreement":
            mock_fields = [
                ContractField(
                    field_name="interest_rate",
                    field_type="percentage",
                    value=5.25,
                    confidence=0.92,
                    page_number=12,
                    text_snippet="Interest rate shall be five point two five percent (5.25%)",
                    table_cell=None
                ),
                ContractField(
                    field_name="maturity_date",
                    field_type="date",
                    value="2025-12-31",
                    confidence=0.88,
                    page_number=15,
                    text_snippet="Maturity date: December 31, 2025",
                    table_cell=None
                )
            ]
        
        return mock_fields
    
    async def _mock_table_extraction(self, file_path: str, table_config: Dict[str, Any]) -> List[ContractField]:
        """Mock table extraction for testing."""
        logger.info(f"Mock table extraction for {file_path}")
        
        # Generate mock table fields
        mock_fields = []
        table_name = table_config.get("name", "fee_schedule")
        
        for i in range(3):  # Mock 3 rows
            field = ContractField(
                field_name=f"{table_name}_row_{i}_amount",
                field_type="currency",
                value=1000.0 + (i * 500),
                confidence=0.85,
                page_number=1,
                text_snippet=f"${1000.0 + (i * 500)}",
                table_cell=f"R{i}C0"
            )
            mock_fields.append(field)
        
        return mock_fields
    
    async def _mock_parallel_extraction(self, file_path: str, field_definitions: List[Dict[str, Any]]) -> List[ContractField]:
        """Mock parallel extraction for testing."""
        logger.info(f"Mock parallel extraction for {file_path}")
        
        all_fields = []
        for field_def in field_definitions:
            field = ContractField(
                field_name=field_def.get("name", "unknown"),
                field_type=field_def.get("type", "string"),
                value=f"mock_value_for_{field_def.get('name', 'unknown')}",
                confidence=0.80,
                page_number=1,
                text_snippet=f"Mock text for {field_def.get('name', 'unknown')}",
                table_cell=None
            )
            all_fields.append(field)
        
        return all_fields
    
    async def _extract_csv_data(self, file_path: str, document_type: str) -> List[ContractField]:
        """Extract data from CSV files."""
        logger.info(f"Extracting CSV data from: {file_path}")
        
        try:
            import pandas as pd
            
            # Read CSV file
            df = pd.read_csv(file_path)
            fields = []
            
            # Extract each row as a field
            for idx, row in df.iterrows():
                for col_name, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        field = ContractField(
                            field_name=f"{col_name}_{idx}",
                            field_type="csv_cell",
                            value=str(value),
                            confidence=1.0,
                            page_number=1,
                            text_snippet=str(value),
                            table_cell=f"R{idx}C{list(df.columns).index(col_name)}",
                            bounding_box=None
                        )
                        fields.append(field)
            
            logger.info(f"Extracted {len(fields)} fields from CSV {file_path}")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting CSV data from {file_path}: {e}")
            return []
