# ComplianceIQ 🛡️

**Agentic AI Compliance Automation and Audit Evidence Platform**

ComplianceIQ is designed to continuously monitor cloud infrastructure, codebase configurations, operational policies, and machine learning model lifecycles against major global regulatory and security compliance frameworks (SOC 2, ISO 27001, GDPR, HIPAA, EU AI Act).

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18.0+ & npm 9.0+
- **Terraform CLI**: 1.5+ (for IaC deployment)
- **Azure CLI**: 2.50+

---

## 🛠️ Environment Setup

### 1. Repository Setup
Clone the repository and set up environment configuration:
```bash
cp .env.example .env
```

### 2. Python Virtual Environment Setup
Create and activate Python virtual environment:
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Install development & pre-commit tools
pip install ruff black pytest pre-commit
```

### 3. Node.js Monorepo Setup
Install workspace dependencies:
```bash
npm install
```

### 4. Setup Pre-Commit Hooks
Activate pre-commit hooks:
```bash
pre-commit install
```

---

## 📁 Repository Topology

```
ComplianceIQ/
├── terraform/                # Infrastructure as Code (Azure $0 / Student Tier)
│   └── modules/
│       ├── storage/          # Azure Storage Account, Queues, WORM Container
│       ├── postgres/         # PostgreSQL B1MS + pgvector
│       ├── cosmos/           # Azure Cosmos DB (Append-Only Audit Trails)
│       ├── identity/         # User-Assigned & System Managed Identities
│       └── container_apps/   # Azure Container Apps Environment
├── services/                 # Backend Microservices & AI Agents
│   ├── collector_agent/      # Async queue-driven evidence collector
│   ├── gap_analysis_agent/   # GPT-4o JSON mode gap evaluation engine
│   ├── remediation_advisor/  # Advisory Terraform / CLI generator
│   ├── policy_rag/           # pgvector similarity search Policy Q&A
│   ├── audit_report_service/ # PDF Audit Package exporter
│   └── orchestrator_api/     # FastAPI Orchestrator API Gateway
└── apps/
    └── hitl_portal/          # Next.js 14 Compliance Officer Review Portal
```

---
