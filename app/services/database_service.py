"""Database service for real data persistence."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for SQLite operations."""
    
    def __init__(self):
        self.connection_string = settings.database_url
    
    def initialize(self):
        """Initialize database connection."""
        try:
            # Test connection and create schema
            with self.get_connection() as conn:
                # Read and execute schema
                schema_path = "database/sqlite_schema.sql"
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema
                conn.executescript(schema_sql)
                conn.commit()
            logger.info("Database connection initialized and schema created")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        logger.info("Database connection closed")
    
    @contextmanager
    def get_connection(self):
        """Get database connection."""
        conn = None
        try:
            conn = sqlite3.connect(self.connection_string.replace("sqlite:///", ""))
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    # Document operations
    def create_document(self, document_data: Dict[str, Any]) -> str:
        """Create a new document record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            import json
            import uuid
            document_id = str(uuid.uuid4())
            query = """
                INSERT INTO documents (id, name, type, investor, file_path, file_size, file_hash, metadata, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (
                    document_id,
                    document_data['name'],
                    document_data['type'],
                    document_data.get('investor'),
                    document_data['file_path'],
                    document_data.get('file_size'),
                    document_data.get('file_hash'),
                    json.dumps(document_data.get('metadata', {})),
                    document_data.get('status', 'pending')
                )
            )
            conn.commit()
            return document_id
    
    def update_document_status(self, document_id: str, status: str, processed_at: Optional[datetime] = None):
        """Update document processing status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                UPDATE documents 
                SET status = ?, processed_at = ?
                WHERE id = ?
            """
            cursor.execute(query, (status, processed_at, document_id))
            conn.commit()
    
    def get_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of documents."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, name, type, investor, uploaded_at, processed_at, status, file_path, file_size
                FROM documents
                ORDER BY uploaded_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, name, type, investor, uploaded_at, processed_at, status, file_path, file_size, metadata
                FROM documents
                WHERE id = ?
            """
            cursor.execute(query, (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Contract version operations
    def create_contract_version(self, version_data: Dict[str, Any]) -> str:
        """Create a new document version."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            import json
            import uuid
            version_id = str(uuid.uuid4())
            query = """
                INSERT INTO document_versions (id, document_id, version_number, created_at, extracted_fields, processing_status, processing_errors)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (
                    version_id,
                    version_data['document_id'],
                    version_data.get('version_number', 1),
                    version_data.get('created_at', datetime.utcnow()),
                    json.dumps(version_data.get('extracted_data', [])),
                    version_data.get('status', 'pending'),
                    json.dumps(version_data.get('processing_errors', []))
                )
            )
            conn.commit()
            return version_id
    
    def update_contract_version(self, version_id: str, extracted_data: Dict[str, Any], status: str):
        """Update contract version with extracted data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            import json
            query = """
                UPDATE contract_versions 
                SET extracted_data = ?, status = ?, processed_at = CURRENT_TIMESTAMP
                WHERE version_id = ?
            """
            cursor.execute(query, (json.dumps(extracted_data), status, version_id))
            conn.commit()
    
    # Alert operations
    def create_alert(self, alert_data: Dict[str, Any]) -> str:
        """Create a new alert record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            import json
            import uuid
            alert_id = str(uuid.uuid4())
            query = """
                INSERT INTO alerts (id, violation_id, severity, status, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (
                    alert_id,
                    alert_data.get('violation_id', ''),
                    alert_data['severity'],
                    alert_data.get('status', 'OPEN'),
                    alert_data.get('message', alert_data.get('title', '')),
                    alert_data.get('created_at', datetime.utcnow())
                )
            )
            conn.commit()
            return alert_id
    
    def get_alerts(self, limit: int = 100, offset: int = 0, severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of alerts with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            
            if severity:
                conditions.append("severity = ?")
                params.append(severity)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
                SELECT 
                    id as alert_id, severity, status, message, created_at,
                    acknowledged_by, acknowledged_at
                FROM alerts
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_alert_status(self, alert_id: str, status: str, acknowledged_by: Optional[str] = None):
        """Update alert status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'ACK':
                query = """
                    UPDATE alerts 
                    SET status = ?, acknowledged_at = CURRENT_TIMESTAMP, acknowledged_by = ?
                    WHERE id = ?
                """
                cursor.execute(query, (status, acknowledged_by, alert_id))
            else:
                query = """
                    UPDATE alerts 
                    SET status = ?
                    WHERE id = ?
                """
                cursor.execute(query, (status, alert_id))
            conn.commit()
    
    # Policy operations
    def create_policy(self, policy_data: Dict[str, Any]) -> str:
        """Create a new policy record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            import json
            import uuid
            policy_id = str(uuid.uuid4())
            query = """
                INSERT INTO policies (id, name, version, description, rules, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (
                    policy_id,
                    policy_data['name'],
                    policy_data.get('version'),
                    policy_data.get('description', ''),
                    json.dumps(policy_data.get('rules', [])),
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            conn.commit()
            return policy_id
    
    def get_policies(self) -> List[Dict[str, Any]]:
        """Get list of policies."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id as policy_id, name, version, description, rules, is_active, created_at, updated_at
                FROM policies
                WHERE is_active = 1
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Dashboard statistics
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total violations (alerts)
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_violations = cursor.fetchone()[0]
            
            # Open violations
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'OPEN'")
            open_violations = cursor.fetchone()[0]
            
            # Resolved violations
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'ACK'")
            resolved_violations = cursor.fetchone()[0]
            
            # High severity violations
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'HIGH'")
            high_severity = cursor.fetchone()[0]
            
            # Contracts processed
            cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'processed'")
            contracts_processed = cursor.fetchone()[0]
            
            return {
                "totalViolations": total_violations or 0,
                "openViolations": open_violations or 0,
                "resolvedViolations": resolved_violations or 0,
                "highSeverityViolations": high_severity or 0,
                "contractsProcessed": contracts_processed or 0,
                "lastUpdated": datetime.utcnow().isoformat()
            }
    
    def get_violations_timeseries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get violations time series data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as count
                FROM alerts
                WHERE created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY day
            """.format(days)
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert to list of dicts and ensure all days are represented
            result = []
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            for i in range(days):
                day_name = day_names[i % 7]
                count = 0
                
                # Find count for this day if it exists
                for row in rows:
                    if row[0]:
                        # Convert string date to datetime and check day name
                        from datetime import datetime
                        date_obj = datetime.strptime(row[0], '%Y-%m-%d')
                        if date_obj.strftime('%a') == day_name:
                            count = row[1]
                            break
                
                result.append({"day": day_name, "count": count})
            
            return result
    

# Global database service instance
database_service = DatabaseService()