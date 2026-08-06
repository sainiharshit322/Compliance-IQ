-- ==========================================================
-- ComplianceIQ Immutability Verification Test Script
-- Spec Reference: docs/specs/03_database_schema.md (Section 4)
-- Purpose: Verify that UPDATE and DELETE on audit_trails are blocked
-- ==========================================================

-- 1. Insert a test audit trail record
INSERT INTO audit_trails (
    id,
    framework_id,
    event_type,
    actor_id,
    actor_type,
    target_entity_id,
    justification_notes,
    client_ip
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000000',
    'EVIDENCE_COLLECTED',
    'id-collector-dev',
    'AGENT',
    'evidence-001',
    'Initial automated evidence collection',
    '127.0.0.1'
);

-- 2. Test UPDATE Operation (Expected Result: EXCEPTION 55000)
-- UPDATE audit_trails SET justification_notes = 'Tampered' WHERE id = '00000000-0000-0000-0000-000000000001';

-- 3. Test DELETE Operation (Expected Result: EXCEPTION 55000)
-- DELETE FROM audit_trails WHERE id = '00000000-0000-0000-0000-000000000001';
