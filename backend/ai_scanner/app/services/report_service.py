import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import UploadFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ai_scanner.app.db.models import Report, Scan


def _upload_dir() -> Path:
    path = Path(os.getenv("UPLOAD_DIR", str(Path.cwd() / "uploads")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_pdf(scan: Scan, report: Report, inspector_name: Optional[str] = None) -> str:
    report_id = report.report_id
    file_path = _upload_dir() / f"{report_id}.pdf"
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Smart Consumable Scanner AI Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Report ID:</b> {report_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Product:</b> {scan.product_name or 'Unknown'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Category:</b> {scan.category.value if scan.category else 'Unknown'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Condition:</b> {scan.condition.value}", styles["Normal"]))
    story.append(Paragraph(f"<b>Confidence:</b> {scan.confidence:.1%}", styles["Normal"]))
    story.append(Paragraph(f"<b>Inspector:</b> {inspector_name or 'Unknown'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Date:</b> {report.generated_at.isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 12))

    findings = scan.findings.split("\n") if scan.findings else []
    data = [["Finding"]] + [[f] for f in findings] or [["No findings recorded"]]
    table = Table(data, colWidths=[400])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)
    doc.build(story)
    return str(file_path)


def generate_csv(scan: Scan, report: Report) -> str:
    file_path = _upload_dir() / f"{report.report_id}.csv"
    data = {
        "report_id": [report.report_id],
        "product_name": [scan.product_name],
        "category": [scan.category.value if scan.category else ""],
        "condition": [scan.condition.value],
        "confidence": [scan.confidence],
        "inspected_at": [scan.created_at.isoformat()],
    }
    pd.DataFrame(data).to_csv(file_path, index=False)
    return str(file_path)


def generate_excel(scan: Scan, report: Report) -> str:
    file_path = _upload_dir() / f"{report.report_id}.xlsx"
    data = {
        "report_id": [report.report_id],
        "product_name": [scan.product_name],
        "category": [scan.category.value if scan.category else ""],
        "condition": [scan.condition.value],
        "confidence": [scan.confidence],
        "inspected_at": [scan.created_at.isoformat()],
    }
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        pd.DataFrame(data).to_excel(writer, index=False)
    return str(file_path)


async def save_upload(upload: UploadFile, scan_id: str) -> str:
    ext = Path(upload.filename or "image.jpg").suffix or ".jpg"
    file_path = _upload_dir() / f"{scan_id}{ext}"
    with open(file_path, "wb") as f:
        content = await upload.read()
        f.write(content)
    return str(file_path)
