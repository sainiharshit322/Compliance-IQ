import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.audit_report_service.exporter import AuditReportExporter
from services.audit_report_service.schemas import AuditPackageRequest, EvidenceManifestItem
from services.collector_agent.models import CollectorType
from services.gap_analysis_agent.schemas import ControlSeverityEnum
from services.orchestrator_api.queue_publisher import AzureQueuePublisher
from services.orchestrator_api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    ComplianceStatusEnum,
    ControlEvidenceResponse,
    EvidenceLogItem,
    EvidenceStatusEnum,
    FrameworkItem,
    FrameworkListResponse,
    GapReportItem,
    GapReportListResponse,
    ScanJobResponse,
    ScanRequest,
)
from services.orchestrator_api.workflow import ComplianceIQWorkflowOrchestrator
from services.policy_rag.schemas import PolicyQARequest
from services.policy_rag.service import PolicyRAGService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator_api")

app = FastAPI(
    title="ComplianceIQ Orchestrator API Gateway",
    version="1.0.0",
    description="Production OpenAPI 3.0 API Gateway for ComplianceIQ Multi-Agent Platform.",
)

orchestrator = ComplianceIQWorkflowOrchestrator()
queue_publisher = AzureQueuePublisher()
rag_service = PolicyRAGService()

# Pre-seeded Frameworks List for API Responses
MOCK_FRAMEWORKS = [
    FrameworkItem(
        id="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        code="SOC2_TYPE2",
        name="SOC 2 Type II Trust Services Criteria",
        version="2022.1",
        description="Security, Availability, and Confidentiality criteria for SaaS providers.",
    ),
    FrameworkItem(
        id="8c2ceb4d-2b6d-4aad-8bdd-1b0d6b2dcb5c",
        code="EU_AI_ACT",
        name="EU Artificial Intelligence Act",
        version="2024.1",
        description="Harmonised rules on AI compliance, risk classification, and human oversight obligations.",
    ),
    FrameworkItem(
        id="7a3deb4d-1b5d-3aad-7bdd-0b0d5b1dcb4b",
        code="ISO_27001",
        name="ISO/IEC 27001:2022 Information Security",
        version="2022",
        description="International standard for Information Security Management Systems (ISMS).",
    ),
    FrameworkItem(
        id="6f4deb4d-0b4d-2aad-6bdd-9a0d4b0dcb3a",
        code="GDPR",
        name="General Data Protection Regulation",
        version="2018",
        description="European Union regulation on data protection and privacy.",
    ),
    FrameworkItem(
        id="5e5deb4d-9a3d-1aad-5bdd-8a0d3b9dcb29",
        code="HIPAA",
        name="Health Insurance Portability and Accountability Act",
        version="2013",
        description="US federal standards for protecting sensitive patient health information (PHI).",
    ),
]

# Pre-seeded Gap Reports List for API Responses
MOCK_GAP_REPORTS = [
    GapReportItem(
        id="gap-001-cc61",
        framework_id="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        control_id="cnt-cc61-storage",
        control_code="CC6.1",
        compliance_status=ComplianceStatusEnum.NON_COMPLIANT,
        risk_score=8.5,
        confidence_score=0.95,
        gap_details={
            "reason": "Target Azure Storage Account lacks infrastructure AES-256 data encryption at rest.",
            "non_compliant_resources": ["/subscriptions/000/.../storageAccounts/stprod01"],
        },
        advisory_remediation="```hcl\nresource \"azurerm_storage_account\" \"example\" {\n  infrastructure_encryption_enabled = true\n}\n```",
    ),
    GapReportItem(
        id="gap-002-mfa",
        framework_id="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        control_id="cnt-cc61-mfa",
        control_code="CC6.1_MFA",
        compliance_status=ComplianceStatusEnum.PARTIAL,
        risk_score=6.0,
        confidence_score=0.90,
        gap_details={
            "reason": "Entra ID tenant has 2 admin users without active Multi-Factor Authentication.",
            "non_compliant_resources": ["admin1@company.com", "devops-lead@company.com"],
        },
        advisory_remediation="az ad user update --id admin1@company.com --mfa-status Enabled",
    ),
    GapReportItem(
        id="gap-003-art14",
        framework_id="8c2ceb4d-2b6d-4aad-8bdd-1b0d6b2dcb5c",
        control_id="cnt-art14-oversight",
        control_code="AI_ACT_ART14",
        compliance_status=ComplianceStatusEnum.NEEDS_HUMAN_REVIEW,
        risk_score=7.0,
        confidence_score=0.72,
        gap_details={
            "reason": "Ambiguous evidence collected for Article 14 human oversight requirement. Confidence < 85%.",
            "non_compliant_resources": ["ca-collector-dev"],
        },
        advisory_remediation="Submit human oversight design manual to Compliance Officer for manual verification.",
    ),
]


class ScanJobExecutionRequest(BaseModel):
    job_id: str = Field(..., description="Unique Scan Job UUID")
    control_code: str = Field(..., description="Target Control Code (e.g. CC6.1)")
    framework: str = Field(..., description="Regulatory Framework (e.g. SOC2_TYPE2)")
    collector_type: CollectorType = Field(..., description="Collector tool type")
    target_resource_id: str = Field(..., description="Target Resource ID or Repo string")
    control_title: Optional[str] = Field("Compliance Control Requirement")
    control_description: Optional[str] = Field("Control requirement verification.")
    severity: Optional[ControlSeverityEnum] = Field(ControlSeverityEnum.HIGH)
    evidence_rule_expression: Optional[Dict[str, Any]] = None


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "orchestrator_api", "version": "1.0.0"}


@app.get(
    "/api/v1/frameworks",
    response_model=FrameworkListResponse,
    summary="List Compliance Frameworks",
    tags=["Frameworks"],
)
def list_frameworks(
    code: Optional[str] = Query(None, description="Filter by framework code"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve all active compliance frameworks supported by ComplianceIQ."""
    filtered = MOCK_FRAMEWORKS
    if code:
        filtered = [f for f in MOCK_FRAMEWORKS if f.code.upper() == code.upper()]

    paginated = filtered[offset : offset + limit]
    return FrameworkListResponse(total=len(filtered), data=paginated)


@app.post(
    "/api/v1/scan",
    response_model=ScanJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Async Evidence Collection",
    tags=["Evidence Collection"],
)
def trigger_scan(req: ScanRequest):
    """Enqueues an asynchronous evidence collection job into Azure Storage Queue 'evidence-jobs'."""
    try:
        res = queue_publisher.enqueue_scan_job(
            framework_id=req.framework_id,
            framework_code=req.framework_code,
            collector_type=req.collector_type.value,
            target_resource_id=req.target_resource_id,
            force_recollect=req.force_recollect,
        )
        return ScanJobResponse(**res)
    except Exception as ex:
        logger.error(f"Error triggering scan job: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enqueue scan job: {str(ex)}")


@app.get(
    "/api/v1/controls/{id}/evidence",
    response_model=ControlEvidenceResponse,
    summary="Fetch Control Evidence Logs",
    tags=["Evidence Collection"],
)
def get_control_evidence(
    id: str,
    status: Optional[EvidenceStatusEnum] = Query(None, description="Filter evidence by status"),
):
    """Retrieve evidence records, cryptographic SHA-256 hashes, and WORM storage links for a control."""
    sample_logs = [
        EvidenceLogItem(
            id=str(uuid4()),
            control_id=id,
            collector_type="AZURE_POLICY",
            source_resource_id="/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
            blob_uri="https://stcomplianceiqdev.blob.core.windows.net/evidence-worm/2026/08/evidence-cc61-001.json",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status=EvidenceStatusEnum.APPROVED,
        ),
        EvidenceLogItem(
            id=str(uuid4()),
            control_id=id,
            collector_type="BLOB_IMMUTABILITY",
            source_resource_id="evidence-worm",
            blob_uri="https://stcomplianceiqdev.blob.core.windows.net/evidence-worm/2026/08/evidence-worm-002.json",
            sha256_hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            status=EvidenceStatusEnum.PENDING_REVIEW if status == EvidenceStatusEnum.PENDING_REVIEW else EvidenceStatusEnum.APPROVED,
        ),
    ]

    if status:
        sample_logs = [log for log in sample_logs if log.status == status]

    return ControlEvidenceResponse(
        control_id=id,
        evidence_count=len(sample_logs),
        evidence_logs=sample_logs,
    )


@app.get(
    "/api/v1/gaps",
    response_model=GapReportListResponse,
    summary="List Gap Reports & Failed Controls",
    tags=["Gap Analysis"],
)
def list_gaps(
    framework_id: Optional[str] = Query(None, description="Filter by target framework UUID"),
    compliance_status: Optional[ComplianceStatusEnum] = Query(None, description="Filter by compliance status"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum risk score filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve non-compliant and failed control evaluations along with risk scores and advisory guidance."""
    filtered = MOCK_GAP_REPORTS

    if framework_id:
        filtered = [g for g in filtered if g.framework_id == framework_id]
    if compliance_status:
        filtered = [g for g in filtered if g.compliance_status == compliance_status]
    if min_risk_score is not None:
        filtered = [g for g in filtered if g.risk_score >= min_risk_score]

    paginated = filtered[offset : offset + limit]
    return GapReportListResponse(total=len(filtered), data=paginated)


@app.post(
    "/api/v1/chat",
    summary="Policy Q&A RAG Query",
    tags=["Policy Q&A RAG"],
)
async def query_policy_rag(req: ChatRequest):
    """Submit a natural language question to Policy Q&A RAG Agent (JSON or SSE Streaming mode)."""
    try:
        rag_request = PolicyQARequest(
            user_query=req.prompt,
            framework_code=req.framework_code,
        )
        rag_response = rag_service.answer_question(rag_request)

        citations = [
            CitationItem(
                framework_code=c.framework_code,
                control_code=c.control_code,
                title=c.title,
                similarity_score=c.similarity_score,
            )
            for c in rag_response.citations
        ]

        if not req.stream:
            return ChatResponse(
                answer=rag_response.answer,
                confidence_score=rag_response.confidence_score,
                citations=citations,
            )

        # Server-Sent Events (SSE) streaming token generator
        async def event_generator():
            words = rag_response.answer.split(" ")
            for word in words:
                event_data = json.dumps({"token": word + " "})
                yield f"data: {event_data}\n\n"
                await asyncio.sleep(0.02)

            citations_payload = [c.model_dump() for c in citations]
            final_data = json.dumps({"done": True, "citations": citations_payload})
            yield f"data: {final_data}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as ex:
        logger.error(f"Error executing Policy Q&A RAG query: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(ex))


@app.get(
    "/api/v1/reports/download/{job_id}",
    summary="Download Audit Readiness Package (.zip)",
    tags=["Audit Reports"],
)
def download_audit_report_package(job_id: str):
    """Generates and downloads a ZIP package containing executive PDF report and sha256_evidence_manifest.json."""
    try:
        pkg_req = AuditPackageRequest(
            job_id=job_id,
            framework_code="SOC2_TYPE2",
            target_resource_id="/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
            compliance_status="NON_COMPLIANT",
            risk_score=8.5,
            confidence_score=0.95,
            advisory_remediation="resource \"azurerm_storage_account\" \"example\" {\n  infrastructure_encryption_enabled = true\n}",
            justification_note="Verified manual exception approval document approved by CISO on 2026-08-11.",
        )
        zip_bytes = AuditReportExporter.create_audit_package_zip(pkg_req)

        filename = f"audit_package_{job_id}.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as ex:
        logger.error(f"Error generating audit report package: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate audit package: {str(ex)}")


@app.post("/api/v1/scan-jobs/execute", tags=["Pipeline Execution"])
def execute_scan_job(req: ScanJobExecutionRequest):
    """Synchronously executes full end-to-end multi-agent pipeline."""
    try:
        pipeline_output = orchestrator.execute_pipeline(
            job_id=req.job_id,
            control_code=req.control_code,
            framework=req.framework,
            collector_type=req.collector_type,
            target_resource_id=req.target_resource_id,
            control_title=req.control_title or "Compliance Control Requirement",
            control_description=req.control_description or "Control requirement verification.",
            severity=req.severity or ControlSeverityEnum.HIGH,
            evidence_rule_expression=req.evidence_rule_expression,
        )
        return pipeline_output.model_dump()
    except Exception as ex:
        logger.error(f"Error executing scan job pipeline: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(ex))
