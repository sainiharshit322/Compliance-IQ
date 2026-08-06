"""
ComplianceIQ - FastAPI Orchestrator API Gateway
Primary entry point for HTTP endpoints (/frameworks, /scan, /evidence, /gaps, /chat).
"""

from fastapi import FastAPI

app = FastAPI(
    title="ComplianceIQ Orchestrator API",
    version="1.0.0",
    description="API Gateway for Compliance Automation & Audit Evidence Platform",
)

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "service": "orchestrator_api"}
