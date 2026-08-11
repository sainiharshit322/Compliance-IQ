from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class ComplianceStatusEnum(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class EvidenceStatusEnum(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


class CollectorTypeEnum(str, Enum):
    AZURE_POLICY = "AZURE_POLICY"
    AZURE_RBAC = "AZURE_RBAC"
    BLOB_IMMUTABILITY = "BLOB_IMMUTABILITY"
    ENTRA_MFA = "ENTRA_MFA"
    GITHUB_PR_RULES = "GITHUB_PR_RULES"
    GITHUB_BRANCH_POLICY = "GITHUB_BRANCH_POLICY"
    KUBERNETES_SPEC = "KUBERNETES_SPEC"
    EU_AI_ACT_DOCS = "EU_AI_ACT_DOCS"


class FrameworkItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    code: str
    name: str
    version: str = "2024.1"
    description: Optional[str] = None
    effective_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FrameworkListResponse(BaseModel):
    total: int
    data: List[FrameworkItem]


class ScanRequest(BaseModel):
    framework_id: Optional[str] = None
    framework_code: Optional[str] = "SOC2_TYPE2"
    collector_type: CollectorTypeEnum = CollectorTypeEnum.AZURE_POLICY
    target_resource_id: Optional[str] = "/subscriptions/000/resourceGroups/rg-complianceiq/providers/Microsoft.Storage/storageAccounts/stprod01"
    force_recollect: bool = False


class ScanJobResponse(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "ENQUEUED"
    queue_name: str = "evidence-jobs"
    message: str = "Evidence collection job enqueued into Azure Queue Storage."
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceLogItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    control_id: str
    collector_type: str
    source_resource_id: Optional[str] = None
    blob_uri: str
    sha256_hash: str
    status: EvidenceStatusEnum = EvidenceStatusEnum.APPROVED
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class ControlEvidenceResponse(BaseModel):
    control_id: str
    evidence_count: int
    evidence_logs: List[EvidenceLogItem]


class GapReportItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    framework_id: str
    control_id: str
    control_code: str
    evidence_id: Optional[str] = None
    compliance_status: ComplianceStatusEnum = ComplianceStatusEnum.NON_COMPLIANT
    risk_score: float = Field(..., ge=0.0, le=10.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    gap_details: Dict[str, Any]
    advisory_remediation: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GapReportListResponse(BaseModel):
    total: int
    data: List[GapReportItem]


class CitationItem(BaseModel):
    framework_code: str
    control_code: str
    title: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User regulatory policy question")
    framework_code: Optional[str] = Field(None, description="Optional framework code filter")
    stream: bool = Field(False, description="Enable Server-Sent Events (SSE) streaming response")


class ChatResponse(BaseModel):
    answer: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    citations: List[CitationItem]
