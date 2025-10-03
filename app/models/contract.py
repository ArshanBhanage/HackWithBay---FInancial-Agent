"""Contract and document models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import hashlib


class DocumentType(str, Enum):
    """Types of financial documents."""
    LPA = "lpa"  # Limited Partnership Agreement
    SIDE_LETTER = "side_letter"
    SUBSCRIPTION_AGREEMENT = "subscription_agreement"
    CREDIT_AGREEMENT = "credit_agreement"
    INSURANCE_POLICY = "insurance_policy"
    AMENDMENT = "amendment"
    RIDER = "rider"
    REGULATORY_FILING = "regulatory_filing"
    OTHER = "other"


class ContractStatus(str, Enum):
    """Status of contract processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    ANALYZED = "analyzed"
    ERROR = "error"


class ContractField(BaseModel):
    """Extracted field from a contract document."""
    field_name: str
    field_type: str
    value: Any
    confidence: float
    page_number: int
    text_snippet: str
    table_cell: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None  # For visual evidence


class ContractVersion(BaseModel):
    """A specific version of a contract document."""
    version_id: str
    contract_id: str
    document_path: str
    document_hash: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    status: ContractStatus = ContractStatus.PENDING
    
    # Extracted data
    extracted_fields: List[ContractField] = []
    raw_text: Optional[str] = None
    
    # Metadata
    file_size: int
    page_count: Optional[int] = None
    processing_errors: List[str] = []
    
    def calculate_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()


class Contract(BaseModel):
    """Main contract entity."""
    contract_id: str
    name: str
    document_type: DocumentType
    description: Optional[str] = None
    
    # Versioning
    current_version: Optional[str] = None
    versions: List[ContractVersion] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Related entities
    related_contracts: List[str] = []  # IDs of related contracts
    beneficiaries: List[str] = []  # IDs of affected beneficiaries
    
    # Status
    is_active: bool = True
    tags: List[str] = []
    
    def get_latest_version(self) -> Optional[ContractVersion]:
        """Get the most recent version of this contract."""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.uploaded_at)
    
    def get_version_by_id(self, version_id: str) -> Optional[ContractVersion]:
        """Get a specific version by ID."""
        for version in self.versions:
            if version.version_id == version_id:
                return version
        return None
    
    def add_version(self, version: ContractVersion) -> None:
        """Add a new version to this contract."""
        self.versions.append(version)
        self.current_version = version.version_id
        self.updated_at = datetime.utcnow()
    
    def get_field_value(self, field_name: str, version_id: Optional[str] = None) -> Optional[Any]:
        """Get the value of a specific field from the latest or specified version."""
        version = self.get_version_by_id(version_id) if version_id else self.get_latest_version()
        if not version:
            return None
        
        for field in version.extracted_fields:
            if field.field_name == field_name:
                return field.value
        return None
    
    def get_field_changes(self, field_name: str, from_version_id: str, to_version_id: str) -> Optional[Dict[str, Any]]:
        """Get changes to a specific field between two versions."""
        from_version = self.get_version_by_id(from_version_id)
        to_version = self.get_version_by_id(to_version_id)
        
        if not from_version or not to_version:
            return None
        
        from_value = None
        to_value = None
        
        for field in from_version.extracted_fields:
            if field.field_name == field_name:
                from_value = field.value
                break
        
        for field in to_version.extracted_fields:
            if field.field_name == field_name:
                to_value = field.value
                break
        
        if from_value is None and to_value is None:
            return None
        
        return {
            "field_name": field_name,
            "from_value": from_value,
            "to_value": to_value,
            "from_version": from_version_id,
            "to_version": to_version_id,
            "changed": from_value != to_value
        }
