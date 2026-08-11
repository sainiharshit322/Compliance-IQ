import io
import zipfile
from fastapi.testclient import TestClient

from services.audit_report_service.exporter import AuditReportExporter
from services.audit_report_service.pdf_generator import PDFReportGenerator
from services.audit_report_service.schemas import AuditPackageRequest, EvidenceManifestItem
from services.orchestrator_api.main import app

client = TestClient(app)


def test_pdf_report_generator():
    req = AuditPackageRequest(
        job_id="test-job-999",
        framework_code="SOC2_TYPE2",
        target_resource_id="/subscriptions/000/resourceGroups/rg-prod",
        compliance_status="NON_COMPLIANT",
        risk_score=8.5,
        confidence_score=0.95,
    )
    pdf_bytes = PDFReportGenerator.generate_pdf_report(req)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic byte header check (%PDF-)
    assert pdf_bytes.startswith(b"%PDF-")


def test_audit_package_zip_exporter():
    req = AuditPackageRequest(
        job_id="test-job-777",
        framework_code="EU_AI_ACT",
        target_resource_id="ca-collector-dev",
        compliance_status="NEEDS_HUMAN_REVIEW",
        risk_score=7.0,
        confidence_score=0.72,
        justification_note="Verified manual exception approval document approved by CISO.",
    )
    zip_bytes = AuditReportExporter.create_audit_package_zip(req)
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 1000

    # Extract ZIP in-memory and verify files
    zip_buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        file_list = zf.namelist()
        assert "audit_package_test-job-777/executive_audit_report.pdf" in file_list
        assert "audit_package_test-job-777/sha256_evidence_manifest.json" in file_list

        manifest_data = zf.read("audit_package_test-job-777/sha256_evidence_manifest.json")
        assert b"EU_AI_ACT" in manifest_data
        assert b"NEEDS_HUMAN_REVIEW" in manifest_data


def test_download_audit_report_endpoint():
    job_id = "test-job-123"
    response = client.get(f"/api/v1/reports/download/{job_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert f"attachment; filename=audit_package_{job_id}.zip" in response.headers["content-disposition"]

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        file_list = zf.namelist()
        assert f"audit_package_{job_id}/executive_audit_report.pdf" in file_list
        assert f"audit_package_{job_id}/sha256_evidence_manifest.json" in file_list
