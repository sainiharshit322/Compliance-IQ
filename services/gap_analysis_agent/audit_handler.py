from datetime import datetime, timezone
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.gap_analysis_agent.schemas import GapAnalysisInput, GapAnalysisOutput

logger = logging.getLogger("gap_analysis_agent.audit_handler")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CosmosAuditDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework_id: str = Field(..., description="Cosmos DB Partition Key")
    control_code: str
    compliance_status: str
    risk_score: float
    confidence_score: int
    reasoning_chain: List[str]
    gap_summary: str
    failed_conditions: List[str]
    sha256_hash: str
    collector_type: str
    flagged_for_hitl: bool
    hitl_status: str = Field(default="NONE")
    hitl_reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now_iso)


class AuditTrailHandler:
    def __init__(self, cosmos_container: Optional[Any] = None):
        self.cosmos_container = cosmos_container

    def format_audit_document(
        self,
        input_data: GapAnalysisInput,
        output_data: GapAnalysisOutput,
    ) -> CosmosAuditDocument:
        """Formats evaluation result into Cosmos DB audit trail document schema."""
        framework_id = input_data.control.framework
        tags = [input_data.control.framework, input_data.control.control_code]

        hitl_status = "NONE"
        if output_data.flagged_for_hitl or output_data.confidence_score < 85:
            hitl_status = "PENDING_REVIEW"
            if "Ambiguous Evidence" not in tags:
                tags.append("Ambiguous Evidence")
            if "HITL_PENDING" not in tags:
                tags.append("HITL_PENDING")

        doc = CosmosAuditDocument(
            framework_id=framework_id,
            control_code=input_data.control.control_code,
            compliance_status=output_data.compliance_status.value,
            risk_score=output_data.risk_score,
            confidence_score=output_data.confidence_score,
            reasoning_chain=output_data.reasoning_chain,
            gap_summary=output_data.gap_details.summary,
            failed_conditions=output_data.gap_details.failed_conditions,
            sha256_hash=input_data.evidence.sha256_hash,
            collector_type=input_data.evidence.collector_type,
            flagged_for_hitl=output_data.flagged_for_hitl or (output_data.confidence_score < 85),
            hitl_status=hitl_status,
            hitl_reason=output_data.hitl_reason,
            tags=tags,
        )
        return doc

    def save_audit_trail(
        self,
        input_data: GapAnalysisInput,
        output_data: GapAnalysisOutput,
    ) -> Dict[str, Any]:
        """Saves evaluation audit document to Cosmos DB container or mock storage."""
        doc = self.format_audit_document(input_data, output_data)
        doc_dict = doc.model_dump()

        if self.cosmos_container:
            try:
                logger.info(f"Writing audit trail document {doc.id} to Cosmos DB...")
                self.cosmos_container.create_item(body=doc_dict)
            except Exception as ex:
                logger.error(f"Failed to write audit document to Cosmos DB: {ex}", exc_info=True)
        else:
            logger.info(f"[Mock Audit Persistence] Created audit record {doc.id} for control '{doc.control_code}' (Tags: {doc.tags})")

        return doc_dict
