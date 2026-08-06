-- ==========================================================
-- ComplianceIQ Initial Framework Seed Data Script
-- Populates the 5 target compliance framework definitions
-- Spec Reference: docs/specs/01_prd.md & 03_database_schema.md
-- ==========================================================

BEGIN;

INSERT INTO frameworks (code, name, version, description, effective_date)
VALUES 
(
    'SOC2_TYPE2', 
    'SOC 2 Type II Trust Services Criteria', 
    '2022.1', 
    'AICPA Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy.', 
    '2022-01-01 00:00:00+00'
),
(
    'ISO_27001_2022', 
    'ISO/IEC 27001:2022 Enterprise ISMS', 
    '2022', 
    'International standard for Information Security Management Systems (ISMS) Annex A Controls.', 
    '2022-10-25 00:00:00+00'
),
(
    'GDPR', 
    'EU General Data Protection Regulation', 
    '2016/679', 
    'Regulation on data protection and privacy for all individuals within the European Union.', 
    '2018-05-25 00:00:00+00'
),
(
    'HIPAA', 
    'Health Insurance Portability and Accountability Act', 
    'Security Rule §164', 
    'US federal standard for protecting sensitive patient health information (PHI).', 
    '2013-03-26 00:00:00+00'
),
(
    'EU_AI_ACT', 
    'EU Artificial Intelligence Act', 
    '2024/1689', 
    'Harmonised rules on Artificial Intelligence for High-Risk AI Systems & Risk Governance.', 
    '2024-08-01 00:00:00+00'
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    version = EXCLUDED.version,
    description = EXCLUDED.description,
    effective_date = EXCLUDED.effective_date,
    updated_at = NOW();

COMMIT;
