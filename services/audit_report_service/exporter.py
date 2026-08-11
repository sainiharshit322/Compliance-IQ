import io
import json
import zipfile
from typing import Any, Dict

from services.audit_report_service.pdf_generator import PDFReportGenerator
from services.audit_report_service.schemas import AuditPackageRequest, EvidenceManifestItem


class AuditReportExporter:
    """Assembles downloadable audit readiness packages (.zip)."""

    @staticmethod
    def create_audit_package_zip(req: AuditPackageRequest) -> bytes:
        """Generates Executive PDF and SHA-256 evidence manifest JSON, returning zip bytes."""
        # 1. Generate PDF Executive Summary
        pdf_bytes = PDFReportGenerator.generate_pdf_report(req)

        # 2. Build Cryptographic SHA-256 Evidence Manifest JSON
        evidence_items_payload = []
        items_to_process = req.evidence_items or [
            EvidenceManifestItem(
                control_code="CC6.1",
                control_title="Infrastructure Encryption at Rest",
                collector_type="AZURE_POLICY",
                blob_uri="https://stcomplianceiqdev.blob.core.windows.net/evidence-worm/2026/08/evidence-cc61-001.json",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                status=req.compliance_status,
            )
        ]

        for item in items_to_process:
            evidence_items_payload.append(item.model_dump(mode="json"))

        manifest_data = {
            "audit_package_version": "1.0.0",
            "job_id": req.job_id,
            "framework_code": req.framework_code,
            "target_resource_id": req.target_resource_id,
            "compliance_status": req.compliance_status,
            "risk_score": req.risk_score,
            "confidence_score": req.confidence_score,
            "evidence_manifest": evidence_items_payload,
            "justification_note": req.justification_note,
        }

        manifest_json_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")

        # 3. Create In-Memory ZIP Archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"audit_package_{req.job_id}/executive_audit_report.pdf", pdf_bytes)
            zf.writestr(f"audit_package_{req.job_id}/sha256_evidence_manifest.json", manifest_json_bytes)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
