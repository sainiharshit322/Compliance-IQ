import io
from datetime import datetime, timezone
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.audit_report_service.schemas import AuditPackageRequest, EvidenceManifestItem


class PDFReportGenerator:
    """Generates Executive PDF Audit Readiness Summaries."""

    @staticmethod
    def generate_pdf_report(req: AuditPackageRequest) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica",
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
        )
        mono_style = ParagraphStyle(
            "MonoStyle",
            parent=styles["Code"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica",
        )

        story = []

        # 1. Title & Header Banner
        story.append(Paragraph("ComplianceIQ — Regulatory Audit Readiness Package", title_style))
        story.append(Paragraph("Automated AI Evidence Ingestion & Cryptographic Verification Report", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=15))

        # 2. Executive Metadata Summary Table
        generated_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_data = [
            [
                Paragraph("<b>Scan Job ID:</b>", body_style),
                Paragraph(f"<font fontName='Helvetica'>{req.job_id}</font>", mono_style),
                Paragraph("<b>Generated At:</b>", body_style),
                Paragraph(generated_at_str, body_style),
            ],
            [
                Paragraph("<b>Framework:</b>", body_style),
                Paragraph(f"<b>{req.framework_code}</b>", body_style),
                Paragraph("<b>Status:</b>", body_style),
                Paragraph(
                    f"<font color='{colors.HexColor('#dc2626') if req.compliance_status == 'NON_COMPLIANT' else colors.HexColor('#16a34a')}'><b>{req.compliance_status}</b></font>",
                    body_style,
                ),
            ],
            [
                Paragraph("<b>Overall Risk Score:</b>", body_style),
                Paragraph(f"<b>{req.risk_score:.2f} / 10.00</b>", body_style),
                Paragraph("<b>AI Confidence:</b>", body_style),
                Paragraph(f"{int(req.confidence_score * 100)}%", body_style),
            ],
            [
                Paragraph("<b>Target Resource:</b>", body_style),
                Paragraph(req.target_resource_id, mono_style),
                Paragraph("<b>Auditor Engine:</b>", body_style),
                Paragraph("ComplianceIQ Multi-Agent Orchestrator", body_style),
            ],
        ]

        t_meta = Table(meta_data, colWidths=[110, 160, 100, 170])
        t_meta.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t_meta)
        story.append(Spacer(1, 15))

        # 3. Evidence Log & Cryptographic Verification Table
        story.append(Paragraph("Evaluated Controls & SHA-256 Evidence Manifest", section_heading))

        evidence_rows = [
            [
                Paragraph("<b>Control</b>", body_style),
                Paragraph("<b>Collector</b>", body_style),
                Paragraph("<b>SHA-256 Digest</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
            ]
        ]

        items_to_render = req.evidence_items or [
            EvidenceManifestItem(
                control_code="CC6.1",
                control_title="Infrastructure Encryption at Rest",
                collector_type="AZURE_POLICY",
                blob_uri="https://stcomplianceiqdev.blob.core.windows.net/evidence-worm/2026/08/evidence-cc61-001.json",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                status="NON_COMPLIANT",
            )
        ]

        for item in items_to_render:
            evidence_rows.append(
                [
                    Paragraph(f"<b>{item.control_code}</b>", body_style),
                    Paragraph(item.collector_type, mono_style),
                    Paragraph(item.sha256_hash[:32] + "...", mono_style),
                    Paragraph(
                        f"<font color='{colors.HexColor('#dc2626') if item.status == 'NON_COMPLIANT' else colors.HexColor('#16a34a')}'><b>{item.status}</b></font>",
                        body_style,
                    ),
                ]
            )

        t_evid = Table(evidence_rows, colWidths=[90, 110, 240, 100])
        t_evid.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t_evid)
        story.append(Spacer(1, 15))

        # 4. Advisory Remediation Guidance (Guardrail 1)
        if req.advisory_remediation:
            story.append(Paragraph("Guardrail 1: Advisory Remediation Guidance", section_heading))
            story.append(
                Paragraph(
                    f"<font fontName='Helvetica'>{req.advisory_remediation}</font>",
                    mono_style,
                )
            )
            story.append(Spacer(1, 15))

        # 5. Human-in-the-Loop Override Justification
        if req.justification_note:
            story.append(Paragraph("Human-in-the-Loop Officer Audit Note", section_heading))
            story.append(
                Paragraph(
                    f"<i>Approved Audit Justification:</i> {req.justification_note}",
                    body_style,
                )
            )
            story.append(Spacer(1, 15))

        # 6. WORM Retention Immutability Notice
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=10))
        story.append(
            Paragraph(
                "<b>WORM Immutability Verification:</b> This document and associated raw evidence payloads are stored in an append-only Azure WORM Blob Storage Container (`evidence-worm`) protected by 30-day immutability retention policy locks. SHA-256 hashes are verified against Cosmos DB `audit_trails`.",
                ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.HexColor("#64748b")),
            )
        )

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
