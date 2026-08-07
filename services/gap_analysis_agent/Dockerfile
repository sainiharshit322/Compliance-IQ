# Multi-Stage Dockerfile for Gap Analysis Agent
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/gap_analysis_agent/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY services/gap_analysis_agent ./services/gap_analysis_agent

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "services.gap_analysis_agent.main"]
