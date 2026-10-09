# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import base64
import io
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import qrcode
from fastapi import UploadFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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


_NOT_DETECTED = "Not detected"


def _field_value(scan: Scan, field: str, value: Optional[str]) -> str:
    """Display value; never invents data for missing fields."""
    status = scan.field_status_map.get(field) if hasattr(scan, "field_status_map") else None
    if value in (None, "", "N/A", "Unknown"):
        return _NOT_DETECTED
    if status == "needs_verification":
        return f"{value} (needs verification)"
    if status == "corrected":
        return f"{value} (corrected)"
    return value


def _date_text(value: Optional[datetime]) -> Optional[str]:
    return value.date().isoformat() if value else None


def _date_details(scan: Scan) -> List[dict]:
    try:
        return json.loads(getattr(scan, "date_details", None) or "[]")
    except ValueError:
        return []


def _ocr_dates_text(scan: Scan) -> str:
    rows = [
        f"{d.get('type')}: '{d.get('matched_text')}' -> {d.get('interpreted')} ({d.get('status')})"
        for d in _date_details(scan)
    ]
    return "; ".join(rows) or "No dates found in label text"


def _first_date(scan: Scan, dtype: str) -> Optional[str]:
    for d in _date_details(scan):
        if d.get("type") == dtype:
            return d.get("interpreted")
    return None


def _latest_signoff(scan: Scan):
    signoffs = list(getattr(scan, "signoffs", None) or [])
    return signoffs[-1] if signoffs else None


def _corrections_text(scan: Scan) -> str:
    return "; ".join(
        f"{c.field}: '{c.original_value}' -> '{c.new_value}' by {c.user_name} at {_format_datetime(c.created_at)} (reason: {c.reason})"
        for c in (getattr(scan, "corrections", None) or [])
    ) or "None"


def _reviews_text(scan: Scan) -> str:
    return "; ".join(
        f"{r.status.value} by {r.reviewer_name or r.requester_name or 'unknown'}"
        f"{' at ' + _format_datetime(r.reviewed_at) if r.reviewed_at else ''}"
        f"{' - ' + r.reviewer_notes if r.reviewer_notes else ''}"
        for r in (getattr(scan, "reviews", None) or [])
    ) or "None"


def _signoff_text(scan: Scan) -> str:
    so = _latest_signoff(scan)
    if not so:
        return "Not signed off"
    text = (
        f"{so.decision.upper()} by {so.full_name} <{so.email}> ({so.role}), typed name '{so.typed_name}', "
        f"at {_format_datetime(so.created_at)}; final result: {so.final_result or 'escalated - none'}"
    )
    if so.override_reason:
        text += f"; override reason: {so.override_reason}"
    if so.comments:
        text += f"; comments: {so.comments}"
    return text + ". Electronic acknowledgement, not a certified digital signature."


def _build_report_rows(scan: Scan, report: Report, inspector_name: Optional[str]) -> list:
    findings_text = scan.findings or ""
    d = _report_dict(scan, report, inspector_name)
    esc = lambda v: str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
    rows = [
        ["Organisation", d["organisation"]],
        ["School / site", d["site"]],
        ["Inspection reference", d["inspection_reference"]],
        ["Product", d["product"]],
        ["Brand", d["brand"]],
        ["Category", d["category"]],
        ["Packaging type", d["packaging_type"]],
        ["Packaging condition", d["packaging_condition"]],
        ["Barcode", d["barcode"]],
        ["Batch / Lot", d["batch"]],
        ["Production date", d["production_date"]],
        ["Packaging date", d["packaging_date"]],
        ["Expiry date", d["expiry_date"]],
        ["Best-before date", d["best_before_date"]],
        ["Dates read from label (OCR)", d["ocr_dates"]],
        ["Date warnings", d["date_warnings"]],
        ["Overall result", d["overall_result"]],
        ["Result reason", d["overall_reason"]],
        ["AI visual condition", d["ai_condition"]],
        ["AI confidence", f"{scan.confidence:.1%}"],
        ["Label OCR confidence", d["label_ocr_confidence"]],
        ["Findings / warnings", findings_text.replace("\n", "<br/>") if findings_text else "None"],
        ["Original OCR text", esc(d["ocr_raw_text"]).replace("\n", "<br/>") or _NOT_DETECTED],
        ["Corrections", esc(d["corrections"])],
        ["Review status", d["review_status"]],
        ["Review history", esc(d["review_history"])],
        ["Inspector", f"{d['inspector']} ({d['inspector_email']})"],
        ["Inspector sign-off", esc(d["signoff"])],
        ["Final result", d["final_result"]],
        ["GPS coordinates", f"{scan.latitude}, {scan.longitude}" if scan.latitude and scan.longitude else "N/A"],
        ["Inspection timestamp (UTC)", d["inspected_at"]],
        ["Report ID", report.report_id],
        ["Report generated (UTC)", d["generated_at"]],
        ["Report generated by", inspector_name or "Unknown"],
    ]
    styles = getSampleStyleSheet()
    return [[k, Paragraph(str(v), styles["BodyText"])] for k, v in rows]


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
    table = Table(data, colWidths=[130, 370])
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
            story.append(Paragraph("<b>Signature image drawn on device (not a certified digital signature)</b>", styles["Heading3"]))
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
    so = _latest_signoff(scan)
    return {
        "report_id": report.report_id,
        "inspection_reference": str(scan.id),
        "organisation": company.name if company else "N/A",
        "site": branch.name if branch else "No site assigned",
        "product": _field_value(scan, "product_name", scan.product_name),
        "brand": _field_value(scan, "brand", getattr(scan, "brand", None) or (brand if brand != "Unknown" else None)),
        "category": scan.category.value if scan.category else _NOT_DETECTED,
        "packaging_type": scan.packaging_type or _NOT_DETECTED,
        "packaging_condition": packaging_condition,
        "barcode": _field_value(scan, "barcode_code", scan.barcode_code),
        "batch": _field_value(scan, "batch_number", scan.batch_number),
        "production_date": _field_value(scan, "production_date", _date_text(scan.production_date)),
        "packaging_date": _first_date(scan, "packaging") or _NOT_DETECTED,
        "expiry_date": _field_value(scan, "expiry_date", _date_text(scan.expiry_date)),
        "best_before_date": _first_date(scan, "best_before") or _NOT_DETECTED,
        "ocr_dates": _ocr_dates_text(scan),
        "date_warnings": ", ".join(getattr(scan, "date_flags", []) or []) or "None",
        "overall_result": getattr(scan, "overall_result", None) or "Not recorded",
        "overall_reason": getattr(scan, "overall_reason", None) or "",
        "ai_condition": scan.condition.value,
        "ai_confidence": scan.confidence,
        "label_ocr_confidence": label_confidence,
        "findings": findings_text,
        "ocr_raw_text": getattr(scan, "ocr_raw_text", None) or "",
        "corrections": _corrections_text(scan),
        "review_status": getattr(scan, "review_status", None) or "Not recorded",
        "review_history": _reviews_text(scan),
        "inspector": scan.inspector_name or "Unknown",
        "inspector_email": scan.inspector_email or "Unknown",
        "signoff": _signoff_text(scan),
        "signoff_by": so.full_name if so else "",
        "signoff_decision": so.decision if so else "",
        "signoff_at": _format_datetime(so.created_at) if so else "",
        "final_result": getattr(scan, "final_result", None) or ("Escalated" if so and so.decision == "escalate" else "Not signed off"),
        "inspector_signature_image_present": bool(report.signature_data),
        "latitude": scan.latitude,
        "longitude": scan.longitude,
        "inspected_at": _format_datetime(scan.created_at),
        "generated_at": _format_datetime(report.generated_at),
        "generated_by": inspector_name or "Unknown",
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


REPORT_COLUMNS = ['report_id', 'inspection_reference', 'organisation', 'site', 'product', 'brand', 'category', 'packaging_type', 'packaging_condition', 'barcode', 'batch', 'production_date', 'packaging_date', 'expiry_date', 'best_before_date', 'ocr_dates', 'date_warnings', 'overall_result', 'overall_reason', 'ai_condition', 'ai_confidence', 'label_ocr_confidence', 'findings', 'ocr_raw_text', 'corrections', 'review_status', 'review_history', 'inspector', 'inspector_email', 'signoff', 'signoff_by', 'signoff_decision', 'signoff_at', 'final_result', 'inspector_signature_image_present', 'latitude', 'longitude', 'inspected_at', 'generated_at', 'generated_by']

BATCH_PDF_COLUMNS = [
    ("Inspected (UTC)", "inspected_at"), ("Site", "site"), ("Product", "product"), ("Brand", "brand"),
    ("Barcode", "barcode"), ("Batch", "batch"), ("Prod. date", "production_date"), ("Expiry", "expiry_date"),
    ("Result", "overall_result"), ("Review", "review_status"), ("Inspector", "inspector"), ("Final / sign-off", "final_result"),
]


def generate_batch(scans: List[Scan], report: Report, fmt: str, generated_by: str, filters: Dict[str, Any], org_name: str) -> str:
    rows = [_report_dict(s, report, generated_by) for s in scans]
    if fmt in ("csv", "excel"):
        df = pd.DataFrame(rows, columns=REPORT_COLUMNS)
        if fmt == "csv":
            file_path = _upload_dir() / f"{report.report_id}.csv"
            df.to_csv(file_path, index=False)
        else:
            file_path = _upload_dir() / f"{report.report_id}.xlsx"
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Inspections")
                pd.DataFrame([{"filter": k, "value": v} for k, v in filters.items()] + [
                    {"filter": "report_id", "value": report.report_id},
                    {"filter": "generated_by", "value": generated_by},
                    {"filter": "generated_at", "value": _format_datetime(report.generated_at)},
                ]).to_excel(writer, index=False, sheet_name="Filters")
        return str(file_path)

    file_path = _upload_dir() / f"{report.report_id}.pdf"
    doc = SimpleDocTemplate(str(file_path), pagesize=landscape(A4), leftMargin=20, rightMargin=20)
    styles = getSampleStyleSheet()
    small = styles["BodyText"].clone("small", fontSize=7, leading=8)
    story = [
        Paragraph("<b>Smart Consumable Scanner AI – Inspection Summary Report</b>", styles["Title"]),
        Paragraph(f"Organisation: {org_name} &nbsp; Report ID: {report.report_id} &nbsp; Generated: {_format_datetime(report.generated_at)} by {generated_by}", styles["Normal"]),
        Paragraph("Filters: " + (", ".join(f"{k}={v}" for k, v in filters.items() if v) or "none"), styles["Normal"]),
        Paragraph(f"Inspections: {len(rows)}. Results come from smartphone images, barcode/label reading and AI screening; they are not a laboratory food-safety test. Sign-offs are electronic acknowledgements, not certified digital signatures.", styles["Normal"]),
        Spacer(1, 8),
    ]
    data = [[Paragraph(f"<b>{h}</b>", small) for h, _ in BATCH_PDF_COLUMNS]]
    for r in rows:
        data.append([Paragraph(str(r[k]), small) for _, k in BATCH_PDF_COLUMNS])
    if len(data) == 1:
        data.append([Paragraph("No inspections match these filters", small)] + [""] * (len(BATCH_PDF_COLUMNS) - 1))
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)
    return str(file_path)


async def save_upload(upload: UploadFile, scan_id: str) -> str:
    ext = Path(upload.filename or "image.jpg").suffix or ".jpg"
    file_path = _upload_dir() / f"{scan_id}{ext}"
    with open(file_path, "wb") as f:
        content = await upload.read()
        f.write(content)
    return str(file_path)
