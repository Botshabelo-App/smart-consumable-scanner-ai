# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import base64
import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import qrcode
from fastapi import UploadFile
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ai_scanner.app.db.models import Report, Scan


def _upload_dir() -> Path:
    path = Path(os.getenv("UPLOAD_DIR", str(Path.cwd() / "uploads")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _format_datetime(value: Optional[datetime]) -> str:
    return value.isoformat() if value else "N/A"


def _qr_image(data: str):
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=1.2 * inch, height=1.2 * inch)


def _safe_image(path: str, width: float = 3 * inch, height: float = 3 * inch):
    try:
        if os.path.exists(path):
            return Image(path, width=width, height=height)
    except Exception:
        pass
    return None


def _extract_from_findings(findings: Optional[str], prefix: str) -> Optional[str]:
    if not findings:
        return None
    for line in findings.split("\n"):
        if line.lower().startswith(prefix.lower()):
            match = re.match(rf"{re.escape(prefix)}\s*[:\-]?\s*(.*)", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return None


def _build_report_rows(scan: Scan, report: Report, inspector_name: Optional[str]) -> list:
    company = getattr(scan, "company", None)
    branch = getattr(scan, "branch", None)
    findings_text = scan.findings or ""
    brand = _extract_from_findings(findings_text, "Brand detected") or getattr(scan, "brand", None) or "Unknown"
    packaging_condition = _extract_from_findings(findings_text, "Packaging condition") or getattr(scan, "packaging_condition", None) or "N/A"
    ocr_conf_text = _extract_from_findings(findings_text, "OCR label confidence")
    label_confidence = ocr_conf_text if ocr_conf_text else (
        f"{getattr(scan, 'label_confidence', 0):.0%}" if getattr(scan, 'label_confidence', None) is not None else "N/A"
    )
    return [
        ["Company", company.name if company else "N/A"],
        ["Branch", branch.name if branch else "N/A"],
        ["Product", scan.product_name or "Unknown"],
        ["Brand", brand],
        ["Category", scan.category.value if scan.category else "Unknown"],
        ["Packaging type", scan.packaging_type or "N/A"],
        ["Packaging condition", packaging_condition],
        ["Batch / Lot", scan.batch_number or "N/A"],
        ["Barcode", scan.barcode_code or "N/A"],
        ["Manufacturing date", _format_datetime(scan.production_date) if scan.production_date else "N/A"],
        ["Expiry date", _format_datetime(scan.expiry_date) if scan.expiry_date else "N/A"],
        ["Condition", scan.condition.value],
        ["AI confidence", f"{scan.confidence:.1%}"],
        ["Label OCR confidence", label_confidence],
        ["AI findings", findings_text.replace("\n", "<br/>") if findings_text else "None"],
        ["Inspector", inspector_name or "Unknown"],
        ["GPS coordinates", f"{scan.latitude}, {scan.longitude}" if scan.latitude and scan.longitude else "N/A"],
        ["Inspection timestamp", _format_datetime(scan.created_at)],
        ["Report ID", report.report_id],
        ["Report generated", _format_datetime(report.generated_at)],
    ]


def generate_pdf(scan: Scan, report: Report, inspector_name: Optional[str] = None) -> str:
    report_id = report.report_id
    file_path = _upload_dir() / f"{report_id}.pdf"
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Smart Consumable Scanner AI – Inspection Report</b>", styles["Title"]))
    story.append(Paragraph("This report is generated from a smartphone-captured image and AI analysis. It records observable packaging characteristics and is not a definitive food-safety laboratory test.", styles["Normal"]))
    story.append(Spacer(1, 12))

    data = _build_report_rows(scan, report, inspector_name)
    table = Table(data, colWidths=[120, 380])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Evidence photo
    photo = _safe_image(scan.image_path or "", width=3 * inch, height=3 * inch)
    if photo:
        story.append(Paragraph("<b>Evidence photograph</b>", styles["Heading3"]))
        story.append(photo)
        story.append(Spacer(1, 12))

    # Signature image (base64 data URI) if provided
    if report.signature_data:
        try:
            header, encoded = report.signature_data.split(",", 1)
            sig_bytes = base64.b64decode(encoded)
            story.append(Paragraph("<b>Digital signature</b>", styles["Heading3"]))
            story.append(Image(io.BytesIO(sig_bytes), width=2 * inch, height=0.8 * inch))
            story.append(Spacer(1, 12))
        except Exception:
            pass
    else:
        story.append(Paragraph("<b>Inspector signature</b>", styles["Heading3"]))
        story.append(Paragraph("____________________________________", styles["Normal"]))
        story.append(Spacer(1, 12))

    # QR code linking to this report
    story.append(Paragraph("<b>Verification QR code</b>", styles["Heading3"]))
    story.append(_qr_image(f"report:{report.report_id}"))

    doc.build(story)
    return str(file_path)


def _report_dict(scan: Scan, report: Report, inspector_name: Optional[str]) -> Dict[str, Any]:
    company = getattr(scan, "company", None)
    branch = getattr(scan, "branch", None)
    findings_text = scan.findings or ""
    brand = _extract_from_findings(findings_text, "Brand detected") or getattr(scan, "brand", None) or "Unknown"
    packaging_condition = _extract_from_findings(findings_text, "Packaging condition") or getattr(scan, "packaging_condition", None) or "N/A"
    ocr_conf_text = _extract_from_findings(findings_text, "OCR label confidence")
    label_confidence = ocr_conf_text if ocr_conf_text else (
        f"{getattr(scan, 'label_confidence', 0):.0%}" if getattr(scan, 'label_confidence', None) is not None else "N/A"
    )
    return {
        "report_id": report.report_id,
        "company": company.name if company else "N/A",
        "branch": branch.name if branch else "N/A",
        "product": scan.product_name or "Unknown",
        "brand": brand,
        "category": scan.category.value if scan.category else "Unknown",
        "packaging_type": scan.packaging_type or "N/A",
        "packaging_condition": packaging_condition,
        "batch": scan.batch_number or "N/A",
        "barcode": scan.barcode_code or "N/A",
        "manufacturing_date": _format_datetime(scan.production_date) if scan.production_date else "N/A",
        "expiry_date": _format_datetime(scan.expiry_date) if scan.expiry_date else "N/A",
        "condition": scan.condition.value,
        "ai_confidence": scan.confidence,
        "label_ocr_confidence": label_confidence,
        "findings": findings_text,
        "inspector": inspector_name or "Unknown",
        "inspector_signature_present": bool(report.signature_data),
        "latitude": scan.latitude,
        "longitude": scan.longitude,
        "inspected_at": _format_datetime(scan.created_at),
        "generated_at": _format_datetime(report.generated_at),
    }


def generate_csv(scan: Scan, report: Report, inspector_name: Optional[str] = None) -> str:
    file_path = _upload_dir() / f"{report.report_id}.csv"
    pd.DataFrame([_report_dict(scan, report, inspector_name)]).to_csv(file_path, index=False)
    return str(file_path)


def generate_excel(scan: Scan, report: Report, inspector_name: Optional[str] = None) -> str:
    file_path = _upload_dir() / f"{report.report_id}.xlsx"
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        pd.DataFrame([_report_dict(scan, report, inspector_name)]).to_excel(writer, index=False)
    return str(file_path)


async def save_upload(upload: UploadFile, scan_id: str) -> str:
    ext = Path(upload.filename or "image.jpg").suffix or ".jpg"
    file_path = _upload_dir() / f"{scan_id}{ext}"
    with open(file_path, "wb") as f:
        content = await upload.read()
        f.write(content)
    return str(file_path)
