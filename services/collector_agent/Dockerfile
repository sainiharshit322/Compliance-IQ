# Multi-Stage Dockerfile for Evidence Collector Agent
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/collector_agent/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY services/collector_agent ./services/collector_agent

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "services.collector_agent.main"]
