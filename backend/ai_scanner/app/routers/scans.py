# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Barcode, Product, Scan, User
from ai_scanner.app.dependencies import require_admin, require_user
from ai_scanner.app.limiter import limiter
from ai_scanner.app.schemas import Condition, ProductCategory, ScanFeedbackPayload, ScanRead, ScanResult
from ai_scanner.app.services.ai_client import AIAnalysisError, ai_client
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.openfoodfacts import lookup_barcode as openfoodfacts_lookup
from ai_scanner.app.services.ocr import OcrExtraction, extract_from_bytes
from ai_scanner.app.services.report_service import save_upload

router = APIRouter()


def _resolve_product_from_barcode(db: Session, code: str, company_id: Optional[uuid.UUID] = None):
    barcode = db.query(Barcode).filter(Barcode.code == code).first()
    if not barcode:
        external = openfoodfacts_lookup(code)
        if external:
            q = db.query(Product).filter(Product.name.ilike(external["name"] or ""))
            if company_id:
                q = q.filter((Product.company_id == company_id) | (Product.company_id.is_(None)))
            product = q.first()
            if not product:
                product = Product(
                    name=external["name"] or "Unknown product",
                    category=None,
                    packaging_type=external.get("packaging"),
                    company_id=company_id,
                )
                db.add(product)
                db.commit()
                db.refresh(product)
            barcode = Barcode(
                product_id=product.id,
                code=code,
                source="openfoodfacts",
            )
            db.add(barcode)
            db.commit()
            db.refresh(barcode)
    return barcode


def _is_admin(user: User) -> bool:
    return user.role.value in {"administrator", "company_admin"}


def _tenant_scope(user: User, requested_company_id: Optional[uuid.UUID] = None, requested_branch_id: Optional[uuid.UUID] = None):
    """Return the (company_id, branch_id) that a scan should be recorded under."""
    company_id = requested_company_id if _is_admin(user) and requested_company_id else user.company_id
    branch_id = requested_branch_id if _is_admin(user) and requested_branch_id else user.branch_id
    return company_id, branch_id


def _discrepancy_reason(
    ai_condition: Condition,
    expiry_date: Optional[datetime],
    production_date: Optional[datetime],
    raw_text: str = "",
) -> Optional[str]:
    if expiry_date and expiry_date > datetime.utcnow() and ai_condition == Condition.EXPIRED:
        return "AI detected expired appearance but printed expiry date is in the future; flagged for review."
    if expiry_date and expiry_date <= datetime.utcnow() and ai_condition == Condition.FRESH:
        return "AI detected fresh appearance but printed expiry date has passed; flagged for review."
    if production_date and expiry_date and production_date > expiry_date:
        return "Production date printed after expiry date; possible label tampering."
    if production_date and production_date > datetime.utcnow():
        return "Production date is in the future; possible label tampering or reprinting."
    if expiry_date and (expiry_date - datetime.utcnow()).days > 1825:
        return "Printed expiry date is more than 5 years in the future; verify authenticity."
    if raw_text and any(k in raw_text.lower() for k in ["relabel", "relabelled", "reprinted", "overprint", "sticker"]):
        return "Label contains relabel/reprint indicators; inspect carefully for tampering."
    return None


def _coalesce_field(form_value, ocr_value):
    return form_value if form_value is not None else ocr_value


def _apply_expiry_logic(
    ai_result: ScanResult, expiry_date: Optional[datetime], production_date: Optional[datetime]
) -> ScanResult:
    """Adjust AI condition when the printed expiry/production date disagrees with image analysis."""
    if not expiry_date:
        return ai_result

    now = datetime.utcnow()
    findings = list(ai_result.findings or [])
    condition = ai_result.condition
    confidence = ai_result.confidence

    if expiry_date < now:
        condition = Condition.EXPIRED
        confidence = max(confidence, 0.95)
        findings.append("Printed expiry date has passed.")
    elif expiry_date <= now + timedelta(days=7):
        if condition != Condition.EXPIRED:
            condition = Condition.NEAR_EXPIRY
            confidence = max(confidence, 0.85)
            findings.append("Printed expiry date is within 7 days.")
    else:
        if condition == Condition.EXPIRED:
            condition = Condition.SUSPICIOUS
            confidence = 0.78
            findings.append("AI detected expired appearance but printed expiry date is in the future; possible label tampering.")

    if production_date and expiry_date and production_date > expiry_date:
        condition = Condition.SUSPICIOUS
        confidence = 0.80
        findings.append("Production date is after the expiry date; possible label tampering.")

    return ScanResult(
        condition=condition,
        confidence=round(confidence, 3),
        product_name=ai_result.product_name,
        category=ai_result.category,
        packaging_type=ai_result.packaging_type,
        findings=findings,
        expiry_risk=ai_result.expiry_risk,
    )


def _normalize_name(name: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _packaging_condition_from_ai(ai_result: ScanResult) -> str:
    if ai_result.condition == Condition.SUSPICIOUS and any(
        f in " ".join(ai_result.findings or []) for f in ["contamination", "damage", "tear", "hole", "dent", "swelling", "leak"]
    ):
        return "damaged / contaminated"
    if ai_result.condition == Condition.EXPIRED:
        return "expired"
    if ai_result.condition == Condition.NEAR_EXPIRY:
        return "near expiry"
    return "intact"


def _enrich_findings(
    ai_result: ScanResult,
    ocr: OcrExtraction,
    barcode_code: Optional[str],
    barcode_product_name: Optional[str],
) -> List[str]:
    """Add human-readable packaging-defect and OCR-quality findings."""
    findings = list(ai_result.findings or [])

    if ocr.label_confidence:
        findings.append(f"OCR label confidence: {ocr.label_confidence:.0%}")

    if ocr.brand:
        findings.append(f"Brand detected: {ocr.brand}")

    if not ocr.raw_text or len(ocr.raw_text.strip()) < 10:
        findings.append("No clear label text detected — verify label is facing camera and readable.")
    elif ocr.expiry_date is None and ocr.batch_number is None:
        findings.append("Expiry or batch information not found on label — manual check recommended.")

    if barcode_code and barcode_product_name and ocr.product_name:
        if _normalize_name(barcode_product_name) not in _normalize_name(ocr.product_name) and _normalize_name(ocr.product_name) not in _normalize_name(barcode_product_name):
            findings.append(
                f"Barcode lookup product '{barcode_product_name}' does not match label product '{ocr.product_name}'; possible counterfeit or barcode mismatch."
            )
            ai_result.condition = Condition.SUSPICIOUS
            ai_result.confidence = max(ai_result.confidence, 0.80)

    if (not barcode_code and not ocr.raw_text) or len(ocr.raw_text.strip()) < 10:
        findings.append("No barcode or readable label detected — possible missing label or packaging damage.")

    findings_text = " ".join(findings).lower()
    damage_keywords = ["tear", "hole", "dent", "swelling", "leak", "crack", "rupture", "puncture", "broken seal"]
    contamination_keywords = ["mould", "mold", "discolouration", "discoloration", "fungus", "slime", "off smell"]
    if any(k in findings_text for k in damage_keywords):
        findings.append("Possible packaging damage detected — inspect manually.")
    if any(k in findings_text for k in contamination_keywords):
        findings.append("Possible contamination detected — inspect manually.")

    packaging_condition = _packaging_condition_from_ai(ai_result)
    findings.append(f"Packaging condition: {packaging_condition}")

    # Cautious final statement: image analysis is never proof of safety or tampering.
    if not ocr.raw_text or len(ocr.raw_text.strip()) < 10:
        findings.append("Limited label information — manual verification recommended.")

    return findings


@router.post("/analyze", response_model=ScanRead)
@limiter.limit("30/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    barcode_code: Optional[str] = Form(None),
    batch_number: Optional[str] = Form(None),
    production_date: Optional[datetime] = Form(None),
    expiry_date: Optional[datetime] = Form(None),
    company_id: Optional[uuid.UUID] = Form(None),
    branch_id: Optional[uuid.UUID] = Form(None),
    device_id: Optional[uuid.UUID] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    # 1. OCR on the captured image to auto-fill packaging fields.
    try:
        image_bytes = await image.read()
        await image.seek(0)
        ocr = extract_from_bytes(image_bytes)
    except Exception:
        ocr = OcrExtraction()

    barcode_code = _coalesce_field(barcode_code, ocr.barcode)
    batch_number = _coalesce_field(batch_number, ocr.batch_number)
    production_date = _coalesce_field(production_date, ocr.production_date)
    expiry_date = _coalesce_field(expiry_date, ocr.expiry_date)
    product_name = _coalesce_field(product_name, ocr.product_name)
    brand = _coalesce_field(brand, ocr.brand)

    # Determine tenant scope for the scan.
    scan_company_id, scan_branch_id = _tenant_scope(user, company_id, branch_id)

    # 2. Resolve product from barcode (OpenFoodFacts fallback).
    barcode_obj = _resolve_product_from_barcode(db, barcode_code, company_id=scan_company_id) if barcode_code else None
    product_id = barcode_obj.product_id if barcode_obj else None
    product = db.query(Product).filter(Product.id == product_id).first() if product_id else None

    hint = product_name or (product.name if product else None) or barcode_code
    try:
        ai_result: ScanResult = await ai_client.analyze_image(image, product_hint=hint)
    except AIAnalysisError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # 3. Apply printed-date and production-date cross-checks.
    ai_result = _apply_expiry_logic(ai_result, expiry_date, production_date)

    # 4. Add packaging-defect and OCR-quality findings.
    barcode_product_name = product.name if product else (barcode_obj.product.name if barcode_obj and barcode_obj.product else None)
    ai_result.findings = _enrich_findings(ai_result, ocr, barcode_code, barcode_product_name)

    product_category = None
    if ai_result.category:
        product_category = ai_result.category
    elif category:
        try:
            product_category = ProductCategory(category.lower())
        except ValueError:
            pass
    elif product and product.category:
        product_category = product.category

    # Prefer user/OCR-provided product name over AI-derived one, since packaging text is authoritative.
    scan_product_name = product_name or ai_result.product_name or (product.name if product else None)
    ocr_expiry = expiry_date or (barcode_obj.expiry_date if barcode_obj else None)
    discrepancy_reason = _discrepancy_reason(
        ai_result.condition, ocr_expiry, production_date, raw_text=ocr.raw_text
    )

    scan = Scan(
        id=uuid.uuid4(),
        product_id=product_id,
        barcode_id=barcode_obj.id if barcode_obj else None,
        company_id=scan_company_id,
        branch_id=scan_branch_id,
        device_id=device_id,
        product_name=scan_product_name,
        category=product_category,
        condition=ai_result.condition,
        confidence=ai_result.confidence,
        packaging_type=ai_result.packaging_type or (product.packaging_type if product else None),
        findings="\n".join(ai_result.findings) if ai_result.findings else "",
        expiry_risk=ai_result.expiry_risk,
        barcode_code=barcode_code,
        batch_number=batch_number,
        production_date=production_date,
        expiry_date=expiry_date,
        ai_vs_label_discrepancy=discrepancy_reason is not None,
        discrepancy_reason=discrepancy_reason,
        latitude=latitude,
        longitude=longitude,
        inspector_id=user.id,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Save image on disk
    await image.seek(0)
    image_path = await save_upload(image, str(scan.id))
    scan.image_path = image_path
    db.commit()
    db.refresh(scan)

    # Attach extra fields to the ORM instance for the response without adding DB columns.
    # Pydantic reads these as attributes.
    brand = brand or scan_product_name
    packaging_condition = _packaging_condition_from_ai(ai_result)
    scan.brand = brand
    scan.packaging_condition = packaging_condition
    scan.label_confidence = ocr.label_confidence
    scan.detected_fields = ocr.fields

    log_event(
        action="scan_created",
        user_id=user.id,
        resource_type="scan",
        resource_id=str(scan.id),
        details=f"condition={scan.condition.value}, confidence={scan.confidence}, product={scan.product_name}",
    )
    return scan


def _scan_query_for_user(db: Session, user: User):
    q = db.query(Scan)
    if not _is_admin(user) and user.company_id:
        q = q.filter(Scan.company_id == user.company_id)
    return q


@router.get("/", response_model=List[ScanRead])
def list_scans(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return (
        _scan_query_for_user(db, user)
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    scan = _scan_query_for_user(db, user).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/{scan_id}/feedback", response_model=ScanRead)
def feedback(
    scan_id: str,
    payload: ScanFeedbackPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    scan = _scan_query_for_user(db, user).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan.inspector_accepted = payload.accepted
    if not payload.accepted:
        scan.override_condition = payload.suggested_condition
        scan.override_reason = payload.reason
        scan.override_notes = payload.notes
    db.commit()
    db.refresh(scan)
    return scan
