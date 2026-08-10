import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from services.collector_agent.models import CollectorType, ScanJobMessage
from services.collector_agent.tools import (
    check_blob_storage_immutability,
    get_entra_id_mfa_status,
    read_github_pr_rules,
    scan_azure_policy_state,
)
from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import (
    ControlContext,
    ControlSeverityEnum,
    EvidenceContext,
    GapAnalysisInput,
)
from services.remediation_advisor.generator import RemediationAdvisorGenerator
from services.remediation_advisor.schemas import RemediationAdvisorInput

logger = logging.getLogger("orchestrator_api.workflow")


class MultiAgentPipelineOutput(BaseModel):
    job_id: str
    control_id: str
    collector_type: str
    target_resource_id: str
    evidence_result: Dict[str, Any]
    gap_analysis_result: Dict[str, Any]
    remediation_result: Optional[Dict[str, Any]] = None
    audit_document: Dict[str, Any]


class ComplianceIQWorkflowOrchestrator:
    def __init__(
        self,
        gap_analysis_engine: Optional[GapAnalysisEngine] = None,
        remediation_generator: Optional[RemediationAdvisorGenerator] = None,
        cosmos_container: Optional[Any] = None,
    ):
        self.gap_analysis_engine = gap_analysis_engine or GapAnalysisEngine(cosmos_container=cosmos_container)
        self.remediation_generator = remediation_generator or RemediationAdvisorGenerator()

    def execute_pipeline(
        self,
        job_id: str,
        control_code: str,
        framework: str,
        collector_type: CollectorType,
        target_resource_id: str,
        control_title: str = "Compliance Control Requirement",
        control_description: str = "Control requirement verification.",
        severity: ControlSeverityEnum = ControlSeverityEnum.HIGH,
        evidence_rule_expression: Optional[Dict[str, Any]] = None,
        subscription_id: str = "00000000-0000-0000-0000-000000000000",
    ) -> MultiAgentPipelineOutput:
        """
        Executes the multi-agent pipeline:
        1. Dispatch Evidence Collector tool.
        2. Evaluate raw evidence with Gap Analysis Agent (Guardrail 2).
        3. Persist formatted audit trail to Cosmos DB.
        4. If NON_COMPLIANT, invoke Remediation Advisor Agent (Guardrail 1).
        """
        logger.info(f"Starting Multi-Agent Workflow for job '{job_id}' (Control: {control_code}, Framework: {framework})...")

        # Step 1: Execute Evidence Collector tool
        evidence_payload = self._dispatch_collector_tool(
            collector_type=collector_type,
            target_resource_id=target_resource_id,
            subscription_id=subscription_id,
        )

        sha256_hash = evidence_payload.get("sha256_hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        # Step 2 & 3: Gap Analysis & Cosmos DB Audit Trail Persistence
        gap_input = GapAnalysisInput(
            control=ControlContext(
                control_code=control_code,
                framework=framework,
                title=control_title,
                description=control_description,
                severity=severity,
                evidence_rule_expression=evidence_rule_expression,
            ),
            evidence=EvidenceContext(
                collector_type=collector_type.value if isinstance(collector_type, CollectorType) else str(collector_type),
                sha256_hash=sha256_hash,
                payload=evidence_payload,
            ),
        )

        gap_output, audit_doc = self.gap_analysis_engine.process_and_audit(gap_input)

        # Step 4: Invoke Remediation Advisor if NON_COMPLIANT
        remediation_res = None
        if gap_output.compliance_status.value == "NON_COMPLIANT":
            logger.info(f"Control {control_code} evaluated as NON_COMPLIANT. Triggering Remediation Advisor...")
            remediation_input = RemediationAdvisorInput(
                control_code=control_code,
                framework=framework,
                failed_conditions=gap_output.gap_details.failed_conditions,
                target_resource_id=target_resource_id,
                gap_summary=gap_output.gap_details.summary,
            )
            remediation_model = self.remediation_generator.generate_remediation(remediation_input)
            remediation_res = remediation_model.model_dump()

        pipeline_output = MultiAgentPipelineOutput(
            job_id=job_id,
            control_id=control_code,
            collector_type=collector_type.value if isinstance(collector_type, CollectorType) else str(collector_type),
            target_resource_id=target_resource_id,
            evidence_result=evidence_payload,
            gap_analysis_result=gap_output.model_dump(),
            remediation_result=remediation_res,
            audit_document=audit_doc,
        )

        logger.info(f"Multi-Agent Workflow pipeline completed for job '{job_id}'. Status: {gap_output.compliance_status.value}")
        return pipeline_output

    def _dispatch_collector_tool(
        self,
        collector_type: CollectorType,
        target_resource_id: str,
        subscription_id: str,
    ) -> Dict[str, Any]:
        c_type = collector_type.value if isinstance(collector_type, CollectorType) else str(collector_type)

        if c_type == "AZURE_POLICY":
            return scan_azure_policy_state(subscription_id=subscription_id)
        elif c_type == "BLOB_IMMUTABILITY":
            res_name = target_resource_id.split("/")[-1] if "/" in target_resource_id else target_resource_id
            return check_blob_storage_immutability(
                subscription_id=subscription_id,
                storage_account_name="stcomplianceiqdev",
                container_name=res_name,
            )
        elif c_type == "ENTRA_MFA":
            return get_entra_id_mfa_status(tenant_id=target_resource_id)
        elif c_type == "GITHUB_PR_RULES":
            owner, repo = ("ComplianceIQ", target_resource_id)
            if "/" in target_resource_id:
                parts = target_resource_id.split("/")
                owner, repo = parts[0], parts[1]
            return read_github_pr_rules(repository_owner=owner, repository_name=repo)
        else:
            return {"is_compliant": True, "collector_type": c_type, "target": target_resource_id}
