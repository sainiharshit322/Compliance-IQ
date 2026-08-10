from typing import List, Optional
from pydantic import BaseModel, Field


class ImpactAnalysis(BaseModel):
    requires_recreation: bool = Field(..., description="True if infrastructure change requires recreating the resource")
    estimated_downtime: str = Field(..., description="Downtime estimate (e.g. 'None', '1-2 hours')")


class RemediationAdvisorInput(BaseModel):
    control_code: str = Field(..., description="Control code (e.g., CC6.1, AI_ACT_ART14)")
    framework: str = Field(..., description="Framework code (e.g., SOC2_TYPE2, EU_AI_ACT)")
    failed_conditions: List[str] = Field(default_factory=list, description="List of failed control conditions")
    target_resource_id: str = Field(..., description="Azure Resource ID, Entra Tenant ID, or GitHub Repo")
    gap_summary: str = Field(..., description="Summary of non-compliance finding")


class RemediationAdvisorOutput(BaseModel):
    control_code: str = Field(..., description="Associated control code")
    advisory_terraform_snippet: str = Field(..., description="Advisory HCL Terraform resource snippet")
    azure_cli_command: str = Field(..., description="Advisory Azure CLI bash command")
    explanation: str = Field(..., description="Explanation of how snippet remediates the compliance gap")
    impact_analysis: ImpactAnalysis = Field(..., description="Impact analysis summary")
