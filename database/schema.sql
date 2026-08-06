-- ==========================================================
-- ComplianceIQ Raw DDL Migration Script
-- Database Engine: PostgreSQL 15+ / Flexible Server
-- Spec Reference: docs/specs/03_database_schema.md
-- ==========================================================

BEGIN;

-- 1. Create Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Create Custom Enum Types
CREATE TYPE control_severity AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW');
CREATE TYPE evidence_status AS ENUM ('PENDING_REVIEW', 'APPROVED', 'REJECTED', 'OVERRIDDEN');
CREATE TYPE compliance_status AS ENUM ('COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NEEDS_HUMAN_REVIEW');
CREATE TYPE actor_type AS ENUM ('AGENT', 'HUMAN_OPERATOR', 'SYSTEM');
CREATE TYPE remediation_status AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED');

-- 3. Table: frameworks
CREATE TABLE frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    effective_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Table: controls
CREATE TABLE controls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
    control_code VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    severity control_severity NOT NULL DEFAULT 'MEDIUM',
    automated BOOLEAN NOT NULL DEFAULT TRUE,
    evidence_rule_expression JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_framework_control UNIQUE (framework_id, control_code)
);

-- 5. Table: evidence_logs
CREATE TABLE evidence_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    control_id UUID NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
    collector_type VARCHAR(50) NOT NULL,
    source_resource_id TEXT NOT NULL,
    blob_uri TEXT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    status evidence_status NOT NULL DEFAULT 'PENDING_REVIEW',
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB
);

-- 6. Table: remediation_plans
CREATE TABLE remediation_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
    control_id UUID NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
    evidence_id UUID REFERENCES evidence_logs(id) ON DELETE SET NULL,
    compliance_status compliance_status NOT NULL DEFAULT 'NEEDS_HUMAN_REVIEW',
    risk_score NUMERIC(3,2) NOT NULL CHECK (risk_score >= 0.00 AND risk_score <= 10.00),
    confidence_score NUMERIC(3,2) NOT NULL DEFAULT 0.85 CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    gap_details JSONB NOT NULL,
    advisory_remediation TEXT NOT NULL,
    status remediation_status NOT NULL DEFAULT 'OPEN',
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Table: audit_trails (Relational Mirror for Cosmos DB)
CREATE TABLE audit_trails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    actor_id VARCHAR(128) NOT NULL,
    actor_type actor_type NOT NULL,
    target_entity_id VARCHAR(128) NOT NULL,
    previous_state JSONB,
    new_state JSONB,
    justification_notes TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_ip VARCHAR(45)
);

-- 8. Performance Indexes (Tuned for B1MS 2GB RAM Footprint)
CREATE INDEX idx_controls_framework_id ON controls(framework_id);
CREATE INDEX idx_controls_category ON controls(category);
CREATE INDEX idx_evidence_control_id ON evidence_logs(control_id);
CREATE INDEX idx_evidence_status ON evidence_logs(status);
CREATE INDEX idx_evidence_sha256 ON evidence_logs(sha256_hash);
CREATE INDEX idx_remediation_framework_id ON remediation_plans(framework_id);
CREATE INDEX idx_remediation_control_id ON remediation_plans(control_id);
CREATE INDEX idx_remediation_compliance_status ON remediation_plans(compliance_status);
CREATE INDEX idx_audit_framework_id ON audit_trails(framework_id);
CREATE INDEX idx_audit_timestamp ON audit_trails(timestamp);
CREATE INDEX idx_audit_target_entity ON audit_trails(target_entity_id);

-- 9. Append-Only Immutability Trigger Setup (03_database_schema.md Section 4)
CREATE OR REPLACE FUNCTION prevent_audit_trail_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'CRITICAL SECURITY VIOLATION: audit_trails records are strictly immutable and cannot be updated or deleted. Attempted operation: %', TG_OP
        USING ERRCODE = '55000';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_trails_immutable
BEFORE UPDATE OR DELETE ON audit_trails
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_trail_mutation();

-- 10. Lightweight pgvector HNSW Index (03_database_schema.md Section 5.2)
CREATE INDEX idx_controls_embedding_hnsw 
ON controls 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

COMMIT;
