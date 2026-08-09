from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ComplianceStatusEnum(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class ControlSeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ControlContext(BaseModel):
    control_code: str = Field(..., description="Control code (e.g., CC6.1, AI_ACT_ART14)")
    framework: str = Field(..., description="Framework code (e.g., SOC2_TYPE2, EU_AI_ACT)")
    title: str = Field(..., description="Control title")
    description: str = Field(..., description="Control description / requirement")
    severity: ControlSeverityEnum = Field(default=ControlSeverityEnum.MEDIUM)
    evidence_rule_expression: Optional[Dict[str, Any]] = Field(None, description="AST rule expression")


class EvidenceContext(BaseModel):
    collector_type: str = Field(..., description="Collector tool name (e.g., AZURE_POLICY, BLOB_IMMUTABILITY)")
    sha256_hash: str = Field(..., description="SHA-256 hash of collected evidence payload")
    payload: Dict[str, Any] = Field(..., description="Raw collected evidence JSON payload")


class GapAnalysisInput(BaseModel):
    control: ControlContext
    evidence: EvidenceContext


class GapDetails(BaseModel):
    summary: str = Field(..., description="Executive summary of compliance finding")
    failed_conditions: List[str] = Field(default_factory=list, description="List of failed control requirement rules")


class GapAnalysisOutput(BaseModel):
    compliance_status: ComplianceStatusEnum
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk score from 0.00 to 10.00")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score from 0 to 100")
    reasoning_chain: List[str] = Field(..., description="Step-by-step evaluation reasoning chain")
    gap_details: GapDetails
    flagged_for_hitl: bool = Field(default=False)
    hitl_reason: Optional[str] = Field(None)

    @field_validator("confidence_score")
    @classmethod
    def check_guardrail_confidence(cls, v: int, info) -> int:
        return v
