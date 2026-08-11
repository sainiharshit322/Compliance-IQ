from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    job_id: str
    framework_code: str
    target_resource_id: str
    compliance_status: str
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    ai_confidence_score: float = Field(..., ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auditor_role: str = "ComplianceIQ Lead Automated Auditor"


class EvidenceManifestItem(BaseModel):
    control_code: str
    control_title: str
    collector_type: str
    blob_uri: str
    sha256_hash: str
    status: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditPackageRequest(BaseModel):
    job_id: str = Field(..., description="Target Scan Job UUID")
    framework_code: str = "SOC2_TYPE2"
    target_resource_id: str = "/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01"
    compliance_status: str = "NON_COMPLIANT"
    risk_score: float = 8.5
    confidence_score: float = 0.95
    evidence_items: List[EvidenceManifestItem] = Field(default_factory=list)
    advisory_remediation: Optional[str] = None
    justification_note: Optional[str] = None
