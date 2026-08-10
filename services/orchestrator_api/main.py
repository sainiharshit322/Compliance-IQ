import logging
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.collector_agent.models import CollectorType
from services.gap_analysis_agent.schemas import ControlSeverityEnum
from services.orchestrator_api.workflow import ComplianceIQWorkflowOrchestrator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator_api")

app = FastAPI(
    title="ComplianceIQ Orchestrator API Gateway",
    version="1.0.0",
    description="Multi-Agent compliance evaluation pipeline orchestrator REST API.",
)

orchestrator = ComplianceIQWorkflowOrchestrator()


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


@app.post("/api/v1/scan-jobs/execute")
def execute_scan_job(req: ScanJobExecutionRequest):
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
