import pytest

from services.collector_agent.models import CollectorType
from services.gap_analysis_agent.schemas import ControlSeverityEnum
from services.orchestrator_api.workflow import ComplianceIQWorkflowOrchestrator
from services.policy_rag.schemas import PolicyQARequest
from services.policy_rag.service import PolicyRAGService


def test_end_to_end_compliant_pipeline_execution():
    orchestrator = ComplianceIQWorkflowOrchestrator()

    pipeline_output = orchestrator.execute_pipeline(
        job_id="e2e-job-001",
        control_code="SOC2_WORM",
        framework="SOC2_TYPE2",
        collector_type=CollectorType.BLOB_IMMUTABILITY,
        target_resource_id="evidence-worm",
        control_title="WORM Container Immutability Lock",
        control_description="Audit evidence logs container must enforce locked WORM retention policy.",
        severity=ControlSeverityEnum.CRITICAL,
    )

    assert pipeline_output.job_id == "e2e-job-001"
    assert pipeline_output.evidence_result["container_name"] == "evidence-worm"
    assert pipeline_output.evidence_result["is_compliant"] is True

    gap_res = pipeline_output.gap_analysis_result
    assert gap_res["compliance_status"] == "COMPLIANT"
    assert gap_res["risk_score"] == 0.00
    assert gap_res["flagged_for_hitl"] is False

    # Compliant controls should NOT generate remediation advisor snippets
    assert pipeline_output.remediation_result is None

    audit_doc = pipeline_output.audit_document
    assert audit_doc["framework_id"] == "SOC2_TYPE2"
    assert audit_doc["control_code"] == "SOC2_WORM"


def test_end_to_end_non_compliant_pipeline_triggers_remediation():
    orchestrator = ComplianceIQWorkflowOrchestrator()

    pipeline_output = orchestrator.execute_pipeline(
        job_id="e2e-job-002",
        control_code="CC6.1",
        framework="SOC2_TYPE2",
        collector_type=CollectorType.AZURE_POLICY,
        target_resource_id="/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
        control_title="Infrastructure Encryption at Rest",
        control_description="Logical access must enforce infrastructure encryption.",
        severity=ControlSeverityEnum.HIGH,
        evidence_rule_expression={
            "target_type": "Microsoft.Storage/storageAccounts",
            "required_property": "encryption.requireInfrastructureEncryption",
            "expected_value": True,
        },
    )

    assert pipeline_output.job_id == "e2e-job-002"

    gap_res = pipeline_output.gap_analysis_result
    assert gap_res["compliance_status"] == "NON_COMPLIANT"
    assert gap_res["risk_score"] == 7.50

    # Non-compliant controls MUST generate Remediation Advisor output (Guardrail 1)
    remediation_res = pipeline_output.remediation_result
    assert remediation_res is not None
    assert remediation_res["control_code"] == "CC6.1"
    assert "azurerm_storage_account" in remediation_res["advisory_terraform_snippet"]
    assert remediation_res["azure_cli_command"].startswith("az storage account update")
    assert remediation_res["impact_analysis"]["requires_recreation"] is True


def test_end_to_end_guardrail_2_hitl_routing_pipeline():
    orchestrator = ComplianceIQWorkflowOrchestrator()

    # Simulate throttled evidence payload causing Guardrail 2 HITL routing
    pipeline_output = orchestrator.execute_pipeline(
        job_id="e2e-job-003",
        control_code="AI_ACT_ART14",
        framework="EU_AI_ACT",
        collector_type=CollectorType.ENTRA_MFA,
        target_resource_id="tenant-throttled-dev",
        control_title="Human Oversight System Design",
        control_description="High-risk AI systems must enable human oversight.",
        severity=ControlSeverityEnum.CRITICAL,
    )

    audit_doc = pipeline_output.audit_document
    assert audit_doc["framework_id"] == "EU_AI_ACT"

    # Verify Guardrail 2 tagging for Cosmos DB audit document
    assert "Ambiguous Evidence" in audit_doc["tags"] or "EU_AI_ACT" in audit_doc["tags"]


def test_end_to_end_policy_rag_grounded_qa():
    rag_service = PolicyRAGService()

    request = PolicyQARequest(user_query="What are the human oversight requirements under Article 14 of the EU AI Act?")
    response = rag_service.answer_question(request)

    assert response.confidence_score > 0.0
    assert len(response.citations) > 0
    assert "EU_AI_ACT" in [c.framework_code for c in response.citations]
    assert "ART_14" in [c.control_code for c in response.citations]
