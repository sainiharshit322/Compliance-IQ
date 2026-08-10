from unittest.mock import MagicMock

from services.gap_analysis_agent.audit_handler import AuditTrailHandler
from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import (
    ControlContext,
    ControlSeverityEnum,
    EvidenceContext,
    GapAnalysisInput,
)


def test_audit_trail_formatting_compliant_evaluation():
    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="CC6.1",
            framework="SOC2_TYPE2",
            title="Infrastructure Encryption at Rest",
            description="Enforce infrastructure encryption.",
            severity=ControlSeverityEnum.HIGH,
            evidence_rule_expression={
                "target_type": "Microsoft.Storage/storageAccounts",
                "required_property": "encryption.requireInfrastructureEncryption",
                "expected_value": True,
            },
        ),
        evidence=EvidenceContext(
            collector_type="AZURE_RBAC",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            payload={"encryption": {"requireInfrastructureEncryption": True}},
        ),
    )

    engine = GapAnalysisEngine()
    output = engine.evaluate(input_data)

    handler = AuditTrailHandler()
    audit_doc = handler.format_audit_document(input_data, output)

    assert audit_doc.framework_id == "SOC2_TYPE2"
    assert audit_doc.control_code == "CC6.1"
    assert audit_doc.compliance_status == "COMPLIANT"
    assert audit_doc.flagged_for_hitl is False
    assert audit_doc.hitl_status == "NONE"
    assert "SOC2_TYPE2" in audit_doc.tags
    assert "CC6.1" in audit_doc.tags


def test_audit_trail_formatting_guardrail_2_tagging():
    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="AI_ACT_ART14",
            framework="EU_AI_ACT",
            title="Human Oversight System Design",
            description="High-risk AI systems must enable human oversight.",
            severity=ControlSeverityEnum.CRITICAL,
        ),
        evidence=EvidenceContext(
            collector_type="AZURE_RBAC",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            payload={"status": "PARTIAL_THROTTLED"},
        ),
    )

    engine = GapAnalysisEngine()
    output = engine.evaluate(input_data)

    handler = AuditTrailHandler()
    audit_doc = handler.format_audit_document(input_data, output)

    # Verify Guardrail 2 tagging: confidence_score (40) < 85 forces Ambiguous Evidence tags and PENDING_REVIEW status
    assert audit_doc.framework_id == "EU_AI_ACT"
    assert audit_doc.confidence_score < 85
    assert audit_doc.flagged_for_hitl is True
    assert audit_doc.hitl_status == "PENDING_REVIEW"
    assert "Ambiguous Evidence" in audit_doc.tags
    assert "HITL_PENDING" in audit_doc.tags


def test_save_audit_trail_cosmos_integration():
    mock_cosmos_container = MagicMock()

    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="CC6.1",
            framework="SOC2_TYPE2",
            title="Infrastructure Encryption at Rest",
            description="Enforce infrastructure encryption.",
            severity=ControlSeverityEnum.HIGH,
        ),
        evidence=EvidenceContext(
            collector_type="AZURE_RBAC",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            payload={"is_compliant": True},
        ),
    )

    engine = GapAnalysisEngine(cosmos_container=mock_cosmos_container)
    output, audit_record = engine.process_and_audit(input_data)

    mock_cosmos_container.create_item.assert_called_once()
    assert audit_record["framework_id"] == "SOC2_TYPE2"
    assert audit_record["control_code"] == "CC6.1"
