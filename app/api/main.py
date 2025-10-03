"""Main FastAPI application for the Financial Contract Drift Monitor."""

import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import os

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

from ..config import settings
from ..services.pathway_service import PathwayService
from ..services.landingai_service import LandingAIService
from ..services.drift_detector import DriftDetector
from ..services.policy_compiler import PolicyCompiler
from ..services.validation_engine import ValidationEngine
from ..services.notification_service import NotificationService
from ..services.database_service import database_service
from ..services.websocket_service import websocket_service
from ..webhooks.handlers import WebhookHandler
from ..models.contract import Contract, ContractVersion, DocumentType
from ..models.alert import Alert, AlertStatus
from ..models.drift import DriftDetection
from ..models.policy import Policy

logger = logging.getLogger(__name__)

# Global service instances
pathway_service: Optional[PathwayService] = None
landingai_service: Optional[LandingAIService] = None
drift_detector: Optional[DriftDetector] = None
policy_compiler: Optional[PolicyCompiler] = None
validation_engine: Optional[ValidationEngine] = None
notification_service: Optional[NotificationService] = None
webhook_handler: Optional[WebhookHandler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global pathway_service, landingai_service, drift_detector, policy_compiler, validation_engine, notification_service, webhook_handler
    
    # Initialize services
    logger.info("Initializing services...")
    pathway_service = PathwayService()
    landingai_service = LandingAIService()
    drift_detector = DriftDetector()
    policy_compiler = PolicyCompiler()
    validation_engine = ValidationEngine()
    notification_service = NotificationService()
    webhook_handler = WebhookHandler(notification_service)
    
    try:
        # Initialize database service
        database_service.initialize()
        logger.info("Database service initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    try:
        # Initialize WebSocket service
        await websocket_service.start()
        logger.info("WebSocket service initialized")
    except Exception as e:
        logger.error(f"WebSocket service initialization failed: {e}")
        raise
    
    # Set up Pathway streams (simplified for now)
    try:
        document_table = pathway_service.setup_document_stream([settings.upload_dir])
        alert_table = pathway_service.setup_alert_stream()
        policy_table = pathway_service.setup_policy_stream()
        
        # Set up validation engine
        validation_engine.setup_operational_data_stream(document_table)
        logger.info("Pathway streams set up successfully")
    except Exception as e:
        logger.warning(f"Pathway setup failed, using mock mode: {e}")
        # Create mock tables for basic functionality
        document_table = None
        alert_table = None
        policy_table = None
    
    # Add document processing callback
    def process_document_callback(version: ContractVersion, document_data: Dict[str, Any]):
        """Process document when it's uploaded."""
        asyncio.create_task(process_uploaded_document(version, document_data))
    
    pathway_service.add_document_processor(process_document_callback)
    
    logger.info("Services initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    try:
        await websocket_service.stop()
        database_service.close()
        if notification_service:
            await notification_service.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("Services shut down")


# Create FastAPI app
app = FastAPI(
    title="Financial Contract Drift Monitor",
    description="An Agent for Continuous Risk Tracking in Evolving Agreements",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


async def process_uploaded_document(version: ContractVersion, document_data: Dict[str, Any]):
    """Process an uploaded document."""
    try:
        logger.info(f"Processing document: {version.document_path}")
        
        # Extract document using LandingAI
        extracted_fields = []
        if landingai_service:
            extracted_fields = await landingai_service.extract_document(
                version.document_path,
                document_data.get("document_type", "other")
            )
        
        # Update document status in database
        database_service.update_document_status(
            document_data['document_id'], 
            'processed', 
            datetime.utcnow()
        )
        
        # Create document version record
        version_data = {
            'document_id': document_data['document_id'],
            'version_number': 1,
            'extracted_data': [field.model_dump() for field in extracted_fields],
            'status': 'processed'
        }
        version_id = database_service.create_contract_version(version_data)
        
        logger.info(f"Document processed successfully: {version_id}")
        
        # Generate sample violations for demo
        await generate_sample_violations(document_data['document_id'], extracted_fields)
        
        # Notify WebSocket clients
        await websocket_service.notify_document_processed({
            "document_id": document_data['document_id'],
            "name": os.path.basename(document_data['path']),
            "status": "processed",
            "type": document_data['document_type'],
            "version_id": version_id
        })
        
        # Update dashboard stats
        stats = database_service.get_dashboard_stats()
        await websocket_service.notify_stats_updated(stats)
        
    except Exception as e:
        logger.error(f"Error processing document {document_data['path']}: {e}")
        database_service.update_document_status(document_data['document_id'], 'error')
        
        # Notify WebSocket clients about the error
        await websocket_service.notify_document_processed({
            "document_id": document_data['document_id'],
            "name": os.path.basename(document_data['path']),
            "status": "error",
            "type": document_data['document_type'],
            "error": str(e)
        })

async def generate_sample_violations(document_id: str, extracted_fields: List[Any]):
    """Generate sample violations for demo purposes."""
    try:
        # Create sample violations based on document type
        violations = []
        
        # Check for fee mismatches
        for field in extracted_fields:
            if 'fee' in field.field_name.lower() and 'csv' in str(field.value):
                # Found a fee in CSV that might conflict
                violation_data = {
                    "violation_id": f"viol_{datetime.utcnow().timestamp()}",
                    "severity": "HIGH",
                    "status": "OPEN",
                    "message": f"Fee mismatch detected: {field.value} in CSV vs expected 1.75%",
                    "created_at": datetime.utcnow()
                }
                alert_id = database_service.create_alert(violation_data)
                violations.append(alert_id)
        
        # Create additional sample violations
        if len(extracted_fields) > 0:
            sample_violations = [
                {
                    "violation_id": f"viol_{datetime.utcnow().timestamp()}_1",
                    "severity": "MEDIUM",
                    "status": "OPEN", 
                    "message": "Reporting deadline discrepancy detected",
                    "created_at": datetime.utcnow()
                },
                {
                    "violation_id": f"viol_{datetime.utcnow().timestamp()}_2",
                    "severity": "LOW",
                    "status": "OPEN",
                    "message": "Minor clause variation found",
                    "created_at": datetime.utcnow()
                }
            ]
            
            for violation_data in sample_violations:
                alert_id = database_service.create_alert(violation_data)
                violations.append(alert_id)
        
        logger.info(f"Generated {len(violations)} violations for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error generating violations: {e}")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with dashboard."""
    return HTMLResponse(content=get_dashboard_html(), status_code=200)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "pathway": pathway_service is not None,
            "landingai": landingai_service is not None,
            "drift_detector": drift_detector is not None,
            "policy_compiler": policy_compiler is not None,
            "validation_engine": validation_engine is not None,
            "notification_service": notification_service is not None
        }
    }


@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_id: Optional[str] = None,
    document_type: Optional[str] = None
):
    """Upload a document for processing."""
    try:
        # Save file
        file_path = f"{settings.upload_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record in database
        document_data = {
            "name": file.filename,
            "type": document_type or "other",
            "investor": contract_id or "unknown",
            "file_path": file_path,
            "file_size": len(content),
            "status": "pending"
        }
        
        document_id = database_service.create_document(document_data)
        
        # Create contract version
        version = ContractVersion(
            version_id=f"v_{datetime.utcnow().timestamp()}",
            contract_id=document_id,
            document_path=file_path,
            document_hash="",  # Will be calculated
            uploaded_at=datetime.utcnow(),
            file_size=len(content),
            status="pending"
        )
        
        # Process document
        background_tasks.add_task(process_uploaded_document, version, {
            "document_id": document_id,
            "document_type": document_type or "other",
            "path": file_path,
            "size": len(content)
        })
        
        # Notify WebSocket clients
        await websocket_service.notify_document_processed({
            "document_id": document_id,
            "name": file.filename,
            "status": "uploaded",
            "type": document_type or "other"
        })
        
        return {
            "message": "Document uploaded successfully",
            "version_id": version.version_id,
            "document_id": document_id,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contracts")
async def create_contract(contract_data: Dict[str, Any]):
    """Create a new contract."""
    try:
        contract = Contract(
            contract_id=contract_data["contract_id"],
            name=contract_data["name"],
            document_type=DocumentType(contract_data.get("document_type", "other")),
            description=contract_data.get("description"),
            beneficiaries=contract_data.get("beneficiaries", []),
            tags=contract_data.get("tags", [])
        )
        
        # In a real implementation, this would be saved to a database
        return {
            "message": "Contract created successfully",
            "contract_id": contract.contract_id
        }
        
    except Exception as e:
        logger.error(f"Error creating contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contracts")
async def list_contracts():
    """List all contracts."""
    try:
        contracts = database_service.get_documents()
        return {
            "contracts": contracts,
            "total": len(contracts)
        }
    except Exception as e:
        logger.error(f"Error fetching contracts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch contracts")


@app.post("/contracts/{contract_id}/detect-drift")
async def detect_contract_drift(
    contract_id: str,
    from_version_id: str,
    to_version_id: str
):
    """Detect drift between contract versions."""
    try:
        if not drift_detector:
            raise HTTPException(status_code=500, detail="Drift detector not available")
        
        # In a real implementation, this would fetch contract from database
        # For now, return a mock response
        detection = DriftDetection(
            detection_id=f"detection_{datetime.utcnow().timestamp()}",
            contract_id=contract_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            status="completed"
        )
        
        return {
            "detection_id": detection.detection_id,
            "contract_id": contract_id,
            "total_changes": detection.total_changes,
            "material_changes": detection.material_changes,
            "high_risk_changes": detection.high_risk_changes
        }
        
    except Exception as e:
        logger.error(f"Error detecting drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/policies/compile")
async def compile_policy(policy_data: Dict[str, Any]):
    """Compile a policy from contracts."""
    try:
        if not policy_compiler:
            raise HTTPException(status_code=500, detail="Policy compiler not available")
        
        # In a real implementation, this would fetch contracts from database
        contracts = []
        
        policy = policy_compiler.compile_policy(contracts, policy_data["policy_id"])
        
        return {
            "policy_id": policy.policy_id,
            "status": policy.status.value,
            "rules_count": len(policy.rules),
            "conflict_checks_count": len(policy.conflict_checks)
        }
        
    except Exception as e:
        logger.error(f"Error compiling policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts")
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """List alerts with optional filtering."""
    try:
        alerts = database_service.get_alerts(limit=limit, severity=severity, status=status)
        return {
            "alerts": alerts,
            "total": len(alerts),
            "filters": {
                "status": status,
                "severity": severity,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        stats = database_service.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")


@app.get("/dashboard/violations-timeseries")
async def get_violations_timeseries(days: int = 7):
    """Get violations time series data."""
    try:
        timeseries = database_service.get_violations_timeseries(days)
        return timeseries
    except Exception as e:
        logger.error(f"Error fetching violations timeseries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch violations timeseries")


@app.get("/policies")
async def list_policies():
    """List all policies."""
    try:
        policies = database_service.get_policies()
        return {
            "policies": policies,
            "total": len(policies)
        }
    except Exception as e:
        logger.error(f"Error fetching policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch policies")


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user_id: str = "system"):
    """Acknowledge an alert."""
    try:
        database_service.update_alert_status(alert_id, "ACK", user_id)
        return {
            "message": f"Alert {alert_id} acknowledged by {user_id}",
            "alert_id": alert_id,
            "status": "acknowledged"
        }
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_service.handle_connection(websocket)


@app.get("/documents/{filename}")
async def get_document(filename: str):
    """Serve demo documents."""
    # Use absolute path from project root
    documents_dir = os.path.join(os.getcwd(), "documents")
    file_path = os.path.join(documents_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document not found: {file_path}")
    
    media_type = "application/pdf" if filename.endswith('.pdf') else "text/csv"
    return FileResponse(file_path, media_type=media_type)


@app.get("/demo/documents")
async def list_demo_documents():
    """List available demo documents."""
    # Simple hardcoded list for now
    documents = [
        {
            "name": "LPA_v3.pdf",
            "size": 1023,
            "type": "PDF",
            "url": "/documents/LPA_v3.pdf"
        },
        {
            "name": "SideLetter_InstitutionA.pdf", 
            "size": 954,
            "type": "PDF",
            "url": "/documents/SideLetter_InstitutionA.pdf"
        },
        {
            "name": "SideLetter_FoundationB.pdf",
            "size": 967,
            "type": "PDF", 
            "url": "/documents/SideLetter_FoundationB.pdf"
        },
        {
            "name": "fees.csv",
            "size": 333,
            "type": "CSV",
            "url": "/documents/fees.csv"
        },
        {
            "name": "reports.csv",
            "size": 301,
            "type": "CSV",
            "url": "/documents/reports.csv"
        }
    ]
    
    return {"documents": documents}


@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user_id: str, notes: Optional[str] = None):
    """Resolve an alert."""
    # In a real implementation, this would update database
    return {
        "message": f"Alert {alert_id} resolved by {user_id}",
        "alert_id": alert_id,
        "status": "resolved",
        "notes": notes
    }


@app.get("/notifications/test")
async def test_notifications():
    """Test notification channels."""
    try:
        if not notification_service:
            raise HTTPException(status_code=500, detail="Notification service not available")
        
        results = await notification_service.test_notification_channels()
        return {
            "message": "Notification test completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoints

@app.post("/webhooks/crm")
async def crm_webhook(request: Request):
    """Handle webhook from CRM system."""
    if not webhook_handler:
        raise HTTPException(status_code=500, detail="Webhook handler not available")
    
    return await webhook_handler.handle_crm_webhook(request)


@app.post("/webhooks/portfolio")
async def portfolio_webhook(request: Request):
    """Handle webhook from portfolio management system."""
    if not webhook_handler:
        raise HTTPException(status_code=500, detail="Webhook handler not available")
    
    return await webhook_handler.handle_portfolio_webhook(request)


@app.post("/webhooks/fund-admin")
async def fund_admin_webhook(request: Request):
    """Handle webhook from fund administration system."""
    if not webhook_handler:
        raise HTTPException(status_code=500, detail="Webhook handler not available")
    
    return await webhook_handler.handle_fund_admin_webhook(request)


def get_dashboard_html() -> str:
    """Generate dashboard HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Financial Contract Drift Monitor</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .content {
                padding: 30px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #667eea;
            }
            .stat-card h3 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 2em;
            }
            .stat-card p {
                margin: 0;
                color: #666;
                font-size: 0.9em;
            }
            .section {
                margin-bottom: 30px;
            }
            .section h2 {
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .upload-area {
                border: 2px dashed #ddd;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                background: #fafafa;
                transition: all 0.3s ease;
            }
            .upload-area:hover {
                border-color: #667eea;
                background: #f0f4ff;
            }
            .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.3s ease;
            }
            .btn:hover {
                background: #5a6fd8;
            }
            .api-info {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 0.9em;
            }
            .api-endpoint {
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 4px;
                border-left: 3px solid #667eea;
            }
            .method {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
                margin-right: 10px;
            }
            .get { background: #e3f2fd; color: #1976d2; }
            .post { background: #e8f5e8; color: #2e7d32; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Financial Contract Drift Monitor</h1>
                <p>An Agent for Continuous Risk Tracking in Evolving Agreements</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <h3>0</h3>
                        <p>Active Contracts</p>
                    </div>
                    <div class="stat-card">
                        <h3>0</h3>
                        <p>Alerts</p>
                    </div>
                    <div class="stat-card">
                        <h3>0</h3>
                        <p>Policies</p>
                    </div>
                    <div class="stat-card">
                        <h3>0</h3>
                        <p>Drift Detections</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Upload Document</h2>
                    <div class="upload-area">
                        <p>Drag and drop a contract document here or click to browse</p>
                        <input type="file" id="fileInput" style="display: none;" accept=".pdf,.doc,.docx">
                        <button class="btn" onclick="document.getElementById('fileInput').click()">Choose File</button>
                    </div>
                </div>
                
                <div class="section">
                    <h2>API Endpoints</h2>
                    <div class="api-info">
                        <div class="api-endpoint">
                            <span class="method get">GET</span>
                            <strong>/health</strong> - Health check
                        </div>
                        <div class="api-endpoint">
                            <span class="method post">POST</span>
                            <strong>/upload</strong> - Upload document
                        </div>
                        <div class="api-endpoint">
                            <span class="method get">GET</span>
                            <strong>/contracts</strong> - List contracts
                        </div>
                        <div class="api-endpoint">
                            <span class="method post">POST</span>
                            <strong>/contracts/{id}/detect-drift</strong> - Detect drift
                        </div>
                        <div class="api-endpoint">
                            <span class="method post">POST</span>
                            <strong>/policies/compile</strong> - Compile policy
                        </div>
                        <div class="api-endpoint">
                            <span class="method get">GET</span>
                            <strong>/alerts</strong> - List alerts
                        </div>
                        <div class="api-endpoint">
                            <span class="method get">GET</span>
                            <strong>/notifications/test</strong> - Test notifications
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // File upload handling
            document.getElementById('fileInput').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    uploadFile(file);
                }
            });
            
            async function uploadFile(file) {
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    alert('File uploaded successfully: ' + result.version_id);
                } catch (error) {
                    alert('Error uploading file: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
