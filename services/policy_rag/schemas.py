from typing import List, Optional
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    framework_code: str = Field(..., description="Regulatory framework code (e.g. SOC2_TYPE2, EU_AI_ACT)")
    control_code: str = Field(..., description="Control code or article number (e.g. CC6.1, ART_14)")
    title: str = Field(..., description="Control title")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")


class PolicyQARequest(BaseModel):
    user_query: str = Field(..., description="User compliance policy query string")
    framework_code: Optional[str] = Field(None, description="Optional target framework filter")
    top_k: int = Field(default=5, description="Number of vector context snippets to retrieve")


class PolicyQAResponse(BaseModel):
    answer: str = Field(..., description="Grounding-enforced AI response string")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.00 to 1.00)")
    citations: List[CitationItem] = Field(default_factory=list, description="Retrieved regulatory control citations")
