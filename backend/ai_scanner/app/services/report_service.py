import base64
import io
import os
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


def _build_report_rows(scan: Scan, report: Report, inspector_name: Optional[str]) -> list:
    company = getattr(scan, "company", None)
    branch = getattr(scan, "branch", None)
    return [
        ["Company", company.name if company else "N/A"],
        ["Branch", branch.name if branch else "N/A"],
        ["Product", scan.product_name or "Unknown"],
        ["Category", scan.category.value if scan.category else "Unknown"],
        ["Packaging", scan.packaging_type or "N/A"],
        ["Batch", scan.batch_number or "N/A"],
        ["Barcode", scan.barcode_code or "N/A"],
        ["Condition", scan.condition.value],
        ["Confidence", f"{scan.confidence:.1%}"],
        ["AI findings", "\n".join(scan.findings.split("\n")) if scan.findings else "None"],
        ["Inspector", inspector_name or "Unknown"],
        ["GPS", f"{scan.latitude}, {scan.longitude}" if scan.latitude and scan.longitude else "N/A"],
        ["Date/Time", _format_datetime(scan.created_at)],
        ["Report ID", report.report_id],
    ]


def generate_pdf(scan: Scan, report: Report, inspector_name: Optional[str] = None) -> str:
    report_id = report.report_id
    file_path = _upload_dir() / f"{report_id}.pdf"
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Smart Consumable Scanner AI – Inspection Report</b>", styles["Title"]))
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

    # QR code linking to this report
    story.append(Paragraph("<b>Verification QR code</b>", styles["Heading3"]))
    story.append(_qr_image(f"report:{report.report_id}"))

    doc.build(story)
    return str(file_path)


def _report_dict(scan: Scan, report: Report, inspector_name: Optional[str]) -> Dict[str, Any]:
    company = getattr(scan, "company", None)
    branch = getattr(scan, "branch", None)
    return {
        "report_id": report.report_id,
        "company": company.name if company else "N/A",
        "branch": branch.name if branch else "N/A",
        "product": scan.product_name or "Unknown",
        "category": scan.category.value if scan.category else "Unknown",
        "packaging": scan.packaging_type or "N/A",
        "batch": scan.batch_number or "N/A",
        "barcode": scan.barcode_code or "N/A",
        "condition": scan.condition.value,
        "confidence": scan.confidence,
        "findings": scan.findings or "",
        "inspector": inspector_name or "Unknown",
        "latitude": scan.latitude,
        "longitude": scan.longitude,
        "inspected_at": _format_datetime(scan.created_at),
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
