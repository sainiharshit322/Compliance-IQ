"""
ComplianceIQ - Gap Analysis Agent Package
Exports GapAnalysisEngine, AuditTrailHandler, and schemas.
"""

from services.gap_analysis_agent.audit_handler import AuditTrailHandler, CosmosAuditDocument
from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import (
    ComplianceStatusEnum,
    ControlContext,
    EvidenceContext,
    GapAnalysisInput,
    GapAnalysisOutput,
)

__all__ = [
    "GapAnalysisEngine",
    "AuditTrailHandler",
    "CosmosAuditDocument",
    "GapAnalysisInput",
    "GapAnalysisOutput",
    "ControlContext",
    "EvidenceContext",
    "ComplianceStatusEnum",
]
