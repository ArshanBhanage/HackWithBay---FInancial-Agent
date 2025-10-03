#!/usr/bin/env python3
"""
Test script to verify Financial Contract Drift Monitor installation.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.config import settings
        print("✓ Config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    try:
        from app.models import Contract, Alert, DriftDetection, Policy
        print("✓ Models imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False
    
    try:
        from app.services import (
            PathwayService, LandingAIService, DriftDetector,
            PolicyCompiler, ValidationEngine, NotificationService
        )
        print("✓ Services imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import services: {e}")
        return False
    
    try:
        from app.webhooks.handlers import WebhookHandler
        print("✓ Webhook handlers imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import webhook handlers: {e}")
        return False
    
    try:
        from app.api.main import app
        print("✓ API application imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import API: {e}")
        return False
    
    return True

def test_directories():
    """Test that required directories exist."""
    print("\nTesting directories...")
    
    required_dirs = [
        "uploads",
        "processed", 
        "streaming_output"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✓ Directory {dir_name} exists")
        else:
            print(f"✗ Directory {dir_name} missing, creating...")
            dir_path.mkdir(exist_ok=True)
            print(f"✓ Directory {dir_name} created")

def test_environment():
    """Test environment configuration."""
    print("\nTesting environment...")
    
    from app.config import settings
    
    # Check critical settings
    if settings.api_host:
        print(f"✓ API host: {settings.api_host}")
    else:
        print("✗ API host not configured")
    
    if settings.api_port:
        print(f"✓ API port: {settings.api_port}")
    else:
        print("✗ API port not configured")
    
    if settings.upload_dir:
        print(f"✓ Upload directory: {settings.upload_dir}")
    else:
        print("✗ Upload directory not configured")
    
    # Check optional settings (without exposing values)
    if settings.landingai_api_key:
        print("✓ LandingAI API key configured")
    else:
        print("⚠ LandingAI API key not configured (will use mock extraction)")
    
    if settings.pathway_api_key:
        print("✓ Pathway API key configured")
    else:
        print("⚠ Pathway API key not configured")
    
    if settings.database_url and settings.database_url != "postgresql://user:password@localhost:5432/financial_contracts":
        print("✓ Database URL configured")
    else:
        print("⚠ Database URL not configured")

def test_models():
    """Test model creation."""
    print("\nTesting models...")
    
    try:
        from app.models.contract import Contract, ContractVersion, DocumentType
        from app.models.alert import Alert, AlertType, AlertSeverity
        from app.models.drift import DriftDetection, DriftChange, ChangeType
        from app.models.policy import Policy, PolicyRule
        from app.models.obligation import Obligation, ObligationType, SeverityLevel
        
        # Test contract creation
        contract = Contract(
            contract_id="test_contract",
            name="Test Contract",
            document_type=DocumentType.LPA
        )
        print("✓ Contract model works")
        
        # Test alert creation
        alert = Alert(
            alert_id="test_alert",
            type=AlertType.DRIFT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="This is a test alert"
        )
        print("✓ Alert model works")
        
        # Test drift detection
        detection = DriftDetection(
            detection_id="test_detection",
            contract_id="test_contract",
            from_version_id="v1",
            to_version_id="v2"
        )
        print("✓ Drift detection model works")
        
        # Test policy
        policy = Policy(
            policy_id="test_policy",
            generated_at="2024-01-10T12:00:00Z",
            source_documents=[]
        )
        print("✓ Policy model works")
        
        # Test obligation
        obligation = Obligation(
            id="test_obligation",
            type=ObligationType.FEE_RATE,
            applies_to="ALL_INVESTORS",
            expected_value=1.75,
            effective_period={"start": "2024-01-01", "end": None},
            evidence={"document_name": "test.pdf", "page_number": 1, "text_snippet": "test"},
            severity=SeverityLevel.HIGH,
            enforcement={"when": "on_fee_calculation", "action": "block_if_mismatch"}
        )
        print("✓ Obligation model works")
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False
    
    return True

def test_services():
    """Test service initialization."""
    print("\nTesting services...")
    
    try:
        from app.services.pathway_service import PathwayService
        from app.services.landingai_service import LandingAIService
        from app.services.drift_detector import DriftDetector
        from app.services.policy_compiler import PolicyCompiler
        from app.services.validation_engine import ValidationEngine
        from app.services.notification_service import NotificationService
        
        # Initialize services
        pathway_service = PathwayService()
        print("✓ Pathway service initialized")
        
        landingai_service = LandingAIService()
        print("✓ LandingAI service initialized")
        
        drift_detector = DriftDetector()
        print("✓ Drift detector initialized")
        
        policy_compiler = PolicyCompiler()
        print("✓ Policy compiler initialized")
        
        validation_engine = ValidationEngine()
        print("✓ Validation engine initialized")
        
        notification_service = NotificationService()
        print("✓ Notification service initialized")
        
    except Exception as e:
        print(f"✗ Service test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Financial Contract Drift Monitor - Installation Test")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_imports()
    test_directories()
    test_environment()
    success &= test_models()
    success &= test_services()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! Installation is working correctly.")
        print("\nTo start the application, run:")
        print("  python main.py")
        print("\nThe API will be available at http://localhost:8000")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
