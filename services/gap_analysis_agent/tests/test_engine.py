from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import (
    ComplianceStatusEnum,
    ControlContext,
    ControlSeverityEnum,
    EvidenceContext,
    GapAnalysisInput,
)


def test_gap_analysis_compliant_evaluation():
    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="CC6.1",
            framework="SOC2_TYPE2",
            title="Infrastructure Encryption at Rest",
            description="Logical access must enforce infrastructure encryption.",
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
            payload={
                "storage_account_name": "stprodcompliance01",
                "encryption": {
                    "requireInfrastructureEncryption": True,
                },
            },
        ),
    )

    engine = GapAnalysisEngine()
    output = engine.evaluate(input_data)

    assert output.compliance_status == ComplianceStatusEnum.COMPLIANT
    assert output.risk_score == 0.00
    assert output.confidence_score >= 85
    assert output.flagged_for_hitl is False
    assert len(output.reasoning_chain) > 0


def test_gap_analysis_non_compliant_evaluation():
    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="CC6.1",
            framework="SOC2_TYPE2",
            title="Infrastructure Encryption at Rest",
            description="Logical access must enforce infrastructure encryption.",
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
            payload={
                "storage_account_name": "stprodcompliance01",
                "encryption": {
                    "requireInfrastructureEncryption": False,
                },
            },
        ),
    )

    engine = GapAnalysisEngine()
    output = engine.evaluate(input_data)

    assert output.compliance_status == ComplianceStatusEnum.NON_COMPLIANT
    assert output.risk_score == 7.50
    assert output.confidence_score >= 85
    assert output.flagged_for_hitl is False
    assert len(output.gap_details.failed_conditions) > 0


def test_guardrail_2_confidence_threshold_routing():
    input_data = GapAnalysisInput(
        control=ControlContext(
            control_code="AI_ACT_ART14",
            framework="EU_AI_ACT",
            title="Human Oversight System Design",
            description="High-risk AI systems must enable natural persons to oversee operation.",
            severity=ControlSeverityEnum.CRITICAL,
        ),
        evidence=EvidenceContext(
            collector_type="AZURE_RBAC",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            payload={
                "status": "PARTIAL_THROTTLED",
                "error_code": "AZURE_ARM_RATE_LIMIT_EXCEEDED",
                "requires_hitl_fallback": True,
            },
        ),
    )

    engine = GapAnalysisEngine()
    output = engine.evaluate(input_data)

    # Verify Guardrail 2 triggered: confidence_score (40) < 85 forces NEEDS_HUMAN_REVIEW and flagged_for_hitl = True
    assert output.confidence_score < 85
    assert output.compliance_status == ComplianceStatusEnum.NEEDS_HUMAN_REVIEW
    assert output.flagged_for_hitl is True
    assert output.hitl_reason is not None
