-- ==========================================================
-- ComplianceIQ Migration 05: Append-Only Trigger & pgvector HNSW Index
-- Spec Reference: docs/specs/03_database_schema.md (Section 4 & 5.2)
-- ==========================================================

BEGIN;

-- 1. Append-Only Immutability Trigger Setup
CREATE OR REPLACE FUNCTION prevent_audit_trail_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'CRITICAL SECURITY VIOLATION: audit_trails records are strictly immutable and cannot be updated or deleted. Attempted operation: %', TG_OP
        USING ERRCODE = '55000';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_trails_immutable ON audit_trails;

CREATE TRIGGER trg_audit_trails_immutable
BEFORE UPDATE OR DELETE ON audit_trails
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_trail_mutation();

-- 2. Lightweight pgvector HNSW Index (Tuned for B1MS 2GB RAM Footprint)
CREATE INDEX IF NOT EXISTS idx_controls_embedding_hnsw 
ON controls 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

COMMIT;
