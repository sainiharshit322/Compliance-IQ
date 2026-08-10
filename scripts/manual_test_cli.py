import json
import sys
from dotenv import load_dotenv

load_dotenv()

from services.collector_agent.models import CollectorType
from services.gap_analysis_agent.schemas import ControlSeverityEnum
from services.orchestrator_api.workflow import ComplianceIQWorkflowOrchestrator
from services.policy_rag.schemas import PolicyQARequest
from services.policy_rag.service import PolicyRAGService


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.center(76)}")
    print("=" * 80 + "\n")


def test_compliant_scan():
    print_banner("TEST 1: Compliant WORM Storage Scan Job Execution")
    orchestrator = ComplianceIQWorkflowOrchestrator()
    output = orchestrator.execute_pipeline(
        job_id="manual-test-001",
        control_code="SOC2_WORM",
        framework="SOC2_TYPE2",
        collector_type=CollectorType.BLOB_IMMUTABILITY,
        target_resource_id="evidence-worm",
        control_title="WORM Container Immutability Lock",
        control_description="Audit evidence logs container must enforce locked WORM retention policy.",
        severity=ControlSeverityEnum.CRITICAL,
    )

    print(">> Evidence Collector Output:")
    print(json.dumps(output.evidence_result, indent=2))
    print("\n>> Gap Analysis Agent Output (Status, Risk Score, Confidence):")
    print(json.dumps(output.gap_analysis_result, indent=2))
    print("\n>> Remediation Result (None expected for compliant controls):", output.remediation_result)
    print("\n>> Cosmos DB Audit Document Tags:", output.audit_document["tags"])


def test_non_compliant_scan_with_remediation():
    print_banner("TEST 2: Non-Compliant Storage Encryption Scan (Triggers Remediation Advisor)")
    orchestrator = ComplianceIQWorkflowOrchestrator()
    output = orchestrator.execute_pipeline(
        job_id="manual-test-002",
        control_code="CC6.1",
        framework="SOC2_TYPE2",
        collector_type=CollectorType.AZURE_POLICY,
        target_resource_id="/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
        control_title="Infrastructure Encryption at Rest",
        control_description="Logical access controls must enforce infrastructure AES-256 data encryption at rest.",
        severity=ControlSeverityEnum.HIGH,
        evidence_rule_expression={
            "target_type": "Microsoft.Storage/storageAccounts",
            "required_property": "encryption.requireInfrastructureEncryption",
            "expected_value": True,
        },
    )

    print(">> Gap Analysis Agent Evaluation:")
    print(f"Status: {output.gap_analysis_result['compliance_status']}")
    print(f"Risk Score: {output.gap_analysis_result['risk_score']}/10.00")
    print(f"Confidence Score: {output.gap_analysis_result['confidence_score']}%")

    print("\n>> Remediation Advisor Agent Output (Guardrail 1 - Strictly Advisory HCL & CLI):")
    rem = output.remediation_result
    if rem:
        print(f"Control Code: {rem['control_code']}")
        print("\n--- Advisory HCL Terraform Snippet ---")
        print(rem["advisory_terraform_snippet"])
        print("\n--- Advisory Azure CLI Command ---")
        print(rem["azure_cli_command"])
        print("\n--- Impact Analysis ---")
        print(f"Requires Recreation: {rem['impact_analysis']['requires_recreation']}")
        print(f"Estimated Downtime: {rem['impact_analysis']['estimated_downtime']}")


def test_guardrail_2_hitl_fallback():
    print_banner("TEST 3: Guardrail 2 (Confidence < 85% HITL Fallback Routing)")
    orchestrator = ComplianceIQWorkflowOrchestrator()
    output = orchestrator.execute_pipeline(
        job_id="manual-test-003",
        control_code="AI_ACT_ART14",
        framework="EU_AI_ACT",
        collector_type=CollectorType.ENTRA_MFA,
        target_resource_id="tenant-throttled-dev",
        control_title="Human Oversight System Design",
        control_description="High-risk AI systems must enable natural persons to oversee operation.",
        severity=ControlSeverityEnum.CRITICAL,
    )

    print(">> Audit Trail Document (Tagged for HITL Portal):")
    print(f"Hitl Status: {output.audit_document['hitl_status']}")
    print(f"Flagged For HITL: {output.audit_document['flagged_for_hitl']}")
    print(f"Hitl Reason: {output.audit_document['hitl_reason']}")
    print(f"Tags: {output.audit_document['tags']}")


def test_policy_qa_rag():
    print_banner("TEST 4: Policy Q&A RAG Agent (Guardrail 3 Grounded Regulatory Citations)")
    service = PolicyRAGService()

    queries = [
        "What are the human oversight requirements under Article 14 of the EU AI Act?",
        "What are the infrastructure encryption requirements for SOC 2 CC6.1?",
        "What is the capital of France?",  # Irrelevant query to test Guardrail 3 fallback
    ]

    for q in queries:
        print(f"\nUser Query: '{q}'")
        res = service.answer_question(PolicyQARequest(user_query=q))
        print(f"Answer: {res.answer}")
        print(f"Confidence Score: {res.confidence_score}")
        print(f"Citations: {[c.framework_code + '-' + c.control_code for c in res.citations]}")


def main():
    print_banner("ComplianceIQ Manual Testing & System Verification Suite")
    test_compliant_scan()
    test_non_compliant_scan_with_remediation()
    test_guardrail_2_hitl_fallback()
    test_policy_qa_rag()
    print_banner("ALL MANUAL TESTS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
