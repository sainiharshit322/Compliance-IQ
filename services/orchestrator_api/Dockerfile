# Multi-Stage Dockerfile for FastAPI Orchestrator API Gateway
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/orchestrator_api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY services/orchestrator_api ./services/orchestrator_api

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "services.orchestrator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
