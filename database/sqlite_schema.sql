-- SQLite Database Schema for Financial Contract Drift Monitor

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    investor TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document versions table
CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_fields TEXT,
    processing_status TEXT DEFAULT 'pending',
    processing_errors TEXT,
    created_at_version TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Policies table
CREATE TABLE IF NOT EXISTS policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    rules TEXT NOT NULL,
    source_documents TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Violations table
CREATE TABLE IF NOT EXISTS violations (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_version_id TEXT,
    rule_id TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_value TEXT,
    actual_value TEXT,
    evidence TEXT NOT NULL,
    diff TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id) ON DELETE CASCADE
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    violation_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,
    FOREIGN KEY (violation_id) REFERENCES violations(id) ON DELETE CASCADE
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    user_id TEXT,
    changes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_investor ON documents(investor);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);

CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_processing_status ON document_versions(processing_status);

CREATE INDEX IF NOT EXISTS idx_violations_document_id ON violations(document_id);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status);
CREATE INDEX IF NOT EXISTS idx_violations_detected_at ON violations(detected_at);

CREATE INDEX IF NOT EXISTS idx_alerts_violation_id ON alerts(violation_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- No default policy - start with clean slate
