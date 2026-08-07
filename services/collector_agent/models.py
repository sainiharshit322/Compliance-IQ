from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollectorType(str, Enum):
    AZURE_POLICY = "AZURE_POLICY"
    BLOB_IMMUTABILITY = "BLOB_IMMUTABILITY"
    ENTRA_MFA = "ENTRA_MFA"
    GITHUB_PR_RULES = "GITHUB_PR_RULES"
    KUBERNETES_SPEC = "KUBERNETES_SPEC"


class ScanJobMessage(BaseModel):
    job_id: str = Field(..., description="Unique Scan Job Execution ID (UUID)")
    control_id: str = Field(..., description="Target Regulatory Control ID (UUID)")
    collector_type: CollectorType = Field(..., description="Type of read-only collector tool to execute")
    target_resource_id: str = Field(..., description="Azure Resource ID, Entra Tenant ID, or GitHub Repo")
    requested_at: datetime = Field(default_factory=utc_now, description="Job creation timestamp")


class CollectionResult(BaseModel):
    job_id: str = Field(..., description="Associated Scan Job Execution ID")
    control_id: str = Field(..., description="Associated Control ID")
    status: str = Field(default="PENDING_REVIEW", description="Evidence status: PENDING_REVIEW, APPROVED, REJECTED")
    collector_type: CollectorType = Field(..., description="Collector tool type")
    source_resource_id: str = Field(..., description="Scanned resource ID")
    blob_uri: Optional[str] = Field(None, description="Immutable WORM Blob Storage URI")
    sha256_hash: Optional[str] = Field(None, description="SHA-256 cryptographic hash of evidence payload")
    collected_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = Field(None, description="Retention boundary timestamp")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Raw JSON data collected")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution metadata")
