"""Pathway service for live document ingestion and streaming."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json

import pathway as pw
from pathway.io import csv
from pathway.udfs import udf

from ..config import settings
from ..models.contract import Contract, ContractVersion, DocumentType, ContractStatus
from ..models.alert import Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class PathwayService:
    """Service for managing Pathway data streams and document ingestion."""
    
    def __init__(self):
        self.runtime_url = settings.pathway_runtime_url
        self.api_key = settings.pathway_api_key
        self.document_table: Optional[pw.Table] = None
        self.alert_table: Optional[pw.Table] = None
        self.policy_table: Optional[pw.Table] = None
        self._callbacks: List[Callable] = []
    
    def setup_document_stream(self, watch_directories: List[str]) -> pw.Table:
        """Set up live document monitoring stream."""
        logger.info(f"Setting up document stream for directories: {watch_directories}")
        
        # Create document table from file system monitoring
        # Use the first directory for now (Pathway fs.read doesn't support multiple directories directly)
        watch_dir = watch_directories[0] if watch_directories else "./uploads"
        
        # Create a simple file monitoring table
        # Since Pathway fs.read has issues, we'll create a manual file watcher
        self.document_table = pw.Table.empty(
            path=str,
            name=str,
            size=int,
            modified=pw.DateTimeNaive,
            is_dir=bool
        )
        
        # Add document processing logic
        self.document_table = self.document_table.select(
            *pw.this,
            document_id=pw.apply_with_type(
                lambda path: self._generate_document_id(path),
                str,
                pw.this.path
            ),
            document_type=pw.apply_with_type(
                lambda name: self._detect_document_type(name),
                str,
                pw.this.name
            ),
            status=pw.cast(str, ContractStatus.PENDING),
                    uploaded_at=pw.this.modified,
                    processed_at=pw.cast(pw.DateTimeNaive, None)
        )
        
        return self.document_table
    
    def setup_alert_stream(self) -> pw.Table:
        """Set up alert streaming table."""
        logger.info("Setting up alert stream")
        
        # Create alert table for streaming alerts
        self.alert_table = pw.Table.empty(
            alert_id=str,
            type=str,
            severity=str,
            title=str,
            description=str,
            contract_id=str,
            created_at=pw.DateTimeNaive,
            status=str
        )
        
        return self.alert_table
    
    def setup_policy_stream(self) -> pw.Table:
        """Set up policy streaming table."""
        logger.info("Setting up policy stream")
        
        # Create policy table for streaming policies
        self.policy_table = pw.Table.empty(
            policy_id=str,
            rules=List[Dict[str, Any]],
            status=str,
            created_at=pw.DateTimeNaive
        )
        
        return self.policy_table
    
    def setup_operational_data_stream(self, data_sources: List[Dict[str, str]]) -> pw.Table:
        """Set up operational data streams (CSV, database, etc.)."""
        logger.info(f"Setting up operational data streams: {data_sources}")
        
        tables = []
        
        for source in data_sources:
            if source["type"] == "csv":
                table = pw.io.csv.read(
                    source["path"],
                    mode="streaming",
                    ignore_errors=True
                )
                tables.append(table)
            elif source["type"] == "json":
                # JSON reading would be implemented here
                logger.warning(f"JSON streaming not yet implemented for {source['name']}")
                continue
            elif source["type"] == "database":
                # Database streaming would be implemented here
                logger.warning(f"Database streaming not yet implemented for {source['name']}")
                continue
        
        if tables:
            # Union all operational data tables
            operational_table = tables[0]
            for table in tables[1:]:
                operational_table = operational_table.union(table)
            
            return operational_table
        
        return pw.Table.empty()
    
    def add_document_processor(self, processor_func: Callable) -> None:
        """Add a document processing callback."""
        self._callbacks.append(processor_func)
    
    def process_document(self, document_data: Dict[str, Any]) -> ContractVersion:
        """Process a single document and return ContractVersion."""
        logger.info(f"Processing document: {document_data['name']}")
        
        # Generate version ID
        version_id = self._generate_version_id(document_data)
        
        # Create contract version
        version = ContractVersion(
            version_id=version_id,
            contract_id=document_data.get("contract_id", "unknown"),
            document_path=document_data["path"],
            document_hash="",  # Will be calculated when file is read
            uploaded_at=document_data["uploaded_at"],
            status=ContractStatus.PROCESSING,
            file_size=document_data["size"],
            page_count=None,
            processing_errors=[]
        )
        
        # Process callbacks
        for callback in self._callbacks:
            try:
                callback(version, document_data)
            except Exception as e:
                logger.error(f"Error in document processor callback: {e}")
                version.processing_errors.append(str(e))
        
        return version
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Create an alert from streaming data."""
        return Alert(
            alert_id=alert_data["alert_id"],
            type=AlertType(alert_data["type"]),
            severity=AlertSeverity(alert_data["severity"]),
            title=alert_data["title"],
            description=alert_data["description"],
            contract_id=alert_data.get("contract_id"),
            created_at=alert_data["created_at"]
        )
    
    def start_streaming(self) -> None:
        """Start Pathway streaming runtime."""
        logger.info("Starting Pathway streaming runtime")
        
        if not self.document_table:
            raise RuntimeError("Document stream not set up. Call setup_document_stream first.")
        
        # Set up streaming output
        pw.io.csv.write(
            self.document_table,
            "./streaming_output/documents.csv"
        )
        
        if self.alert_table:
            pw.io.csv.write(
                self.alert_table,
                "./streaming_output/alerts.csv"
            )
        
        # Start the runtime
        pw.run()
    
    def _generate_document_id(self, path: str) -> str:
        """Generate unique document ID from path."""
        import hashlib
        return hashlib.md5(path.encode()).hexdigest()[:16]
    
    def _generate_version_id(self, document_data: Dict[str, Any]) -> str:
        """Generate unique version ID."""
        import hashlib
        content = f"{document_data['path']}_{document_data['modified']}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _detect_document_type(self, filename: str) -> str:
        """Detect document type from filename."""
        filename_lower = filename.lower()
        
        if "lpa" in filename_lower or "limited_partnership" in filename_lower:
            return DocumentType.LPA
        elif "side_letter" in filename_lower or "sideletter" in filename_lower:
            return DocumentType.SIDE_LETTER
        elif "subscription" in filename_lower:
            return DocumentType.SUBSCRIPTION_AGREEMENT
        elif "credit" in filename_lower or "loan" in filename_lower:
            return DocumentType.CREDIT_AGREEMENT
        elif "insurance" in filename_lower or "policy" in filename_lower:
            return DocumentType.INSURANCE_POLICY
        elif "amendment" in filename_lower:
            return DocumentType.AMENDMENT
        elif "rider" in filename_lower:
            return DocumentType.RIDER
        elif "filing" in filename_lower or "regulatory" in filename_lower:
            return DocumentType.REGULATORY_FILING
        else:
            return DocumentType.OTHER
    
    def stop_streaming(self) -> None:
        """Stop Pathway streaming runtime."""
        logger.info("Stopping Pathway streaming runtime")
        # Pathway runtime will be stopped when the process exits
        pass
