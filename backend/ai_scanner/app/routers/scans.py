# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import json
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Barcode, InspectionSignoff, Product, Scan, ScanCorrection, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.limiter import limiter
from ai_scanner.app.schemas import (
    Condition, InspectionFilters, ProductCategory, ScanCorrectionCreate, ScanDetail,
    ScanFeedbackPayload, ScanRead, ScanResult, SignoffCreate,
)
from ai_scanner.app.services.ai_client import AIAnalysisError, ai_client
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.inspection import (
    ACKNOWLEDGEMENT_TEXT, ATTENTION_RESULTS, apply_filters, get_scan_for_user, scan_query_for_user,
)
from ai_scanner.app.services.openfoodfacts import lookup_barcode as openfoodfacts_lookup
from ai_scanner.app.services.ocr import OcrExtraction, decode_barcodes, extract_from_bytes
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
    """Only platform administrators see across organisations; company admins stay scoped."""
    return user.role.value == "administrator"


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


def _barcode_identity_confirmed(barcode_product_name: str, ocr: OcrExtraction, ai_result: ScanResult) -> bool:
    tokens = [t for t in re.findall(r"[a-z]{4,}", barcode_product_name.lower())]
    evidence = " ".join([ocr.raw_text or "", ocr.product_name or "", ocr.brand or "", ai_result.product_name or ""]).lower()
    evidence = re.sub(r"[^a-z]", "", evidence)
    return any(t in evidence for t in tokens) if tokens else True


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
                f"Barcode/label mismatch: barcode lookup product '{barcode_product_name}' does not match label product '{ocr.product_name}'; manual verification required (not proof of counterfeit)."
            )
            ai_result.condition = Condition.SUSPICIOUS
            ai_result.confidence = max(ai_result.confidence, 0.80)

    if (not barcode_code and not ocr.raw_text) or len(ocr.raw_text.strip()) < 10:
        findings.append("No barcode or readable label detected — possible missing label or packaging damage.")

    findings_text = " ".join(findings).lower()
    damage_keywords = ["tear", "hole", "dent", "swelling", "leak", "crack", "rupture", "puncture", "broken seal"]
    contamination_keywords = ["mould", "mold", "discolouration", "discoloration", "fungus", "slime", "off smell"]
    if any(re.search(rf"\b{k}\b", findings_text) for k in damage_keywords):
        findings.append("Possible packaging damage detected — inspect manually.")
    if any(re.search(rf"\b{k}\b", findings_text) for k in contamination_keywords):
        findings.append("Possible contamination detected — inspect manually.")

    packaging_condition = _packaging_condition_from_ai(ai_result)
    findings.append(f"Packaging condition: {packaging_condition}")

    if barcode_code and barcode_product_name and not _barcode_identity_confirmed(barcode_product_name, ocr, ai_result):
        findings.append(
            f"Barcode/label mismatch: barcode product '{barcode_product_name}' could not be confirmed from the photo or label text; manual verification required (not proof of counterfeit)."
        )

    if barcode_code:
        findings.append("Barcode/QR identifies the product only; it is not proof of safety or authenticity.")

    # Cautious final statement: image analysis is never proof of safety or tampering.
    if not ocr.raw_text or len(ocr.raw_text.strip()) < 10:
        findings.append("Limited label information — manual verification recommended.")

    return findings


PACKAGED_CATEGORIES = {
    ProductCategory.PACKAGED, ProductCategory.DAIRY, ProductCategory.BEVERAGE,
    ProductCategory.FROZEN, ProductCategory.DRY,
}


def _overall_result(
    ai_result: ScanResult,
    ocr: OcrExtraction,
    barcode_code: Optional[str],
    expiry_date: Optional[datetime],
    discrepancy_reason: Optional[str],
    category: Optional[ProductCategory],
    expiry_unverified: bool = False,
):
    """Fuse visual AI, barcode/QR and OCR evidence into a cautious overall result."""
    label_readable = bool(ocr.raw_text and len(ocr.raw_text.strip()) >= 10)
    ai_identified = bool(ai_result.product_name) and ai_result.product_name != "unknown product"
    text = " ".join(ai_result.findings or []).lower()

    if not label_readable and not barcode_code and (not ai_identified or ai_result.confidence < 0.5):
        return "INSUFFICIENT_DATA", "Product could not be identified from photo, barcode or label; rescan or inspect manually."
    if expiry_date and expiry_date < datetime.utcnow():
        return "WARNING", "Printed expiry date has passed."
    packaged = category in PACKAGED_CATEGORIES
    if "possible packaging damage" in text or "possible contamination" in text:
        if packaged:
            return "REVIEW", "Visual damage/contamination indicators on printed packaging (unconfirmed); inspect manually."
        return "WARNING", "Visible damage or contamination indicators; inspect manually."
    if ai_result.condition == Condition.EXPIRED:
        if packaged:
            return "REVIEW", "Visual AI flagged spoilage appearance on sealed packaging, which a camera cannot confirm; inspect manually."
        return "WARNING", "Visual AI indicates spoilage appearance; inspect manually."
    if discrepancy_reason or "mismatch" in text or ai_result.condition == Condition.SUSPICIOUS:
        return "REVIEW", discrepancy_reason or "Evidence is inconsistent or suspicious; manual review required."
    if ai_result.condition == Condition.NEAR_EXPIRY:
        return "REVIEW", "Product is near its expiry date."
    if expiry_unverified:
        return "REVIEW", "Expiry/best-before date was read but needs verification; check the label manually."
    if packaged and not expiry_date:
        return "REVIEW", "Expiry/best-before date not readable; check the label manually."
    if ai_result.confidence < 0.85:
        return "REVIEW", "AI confidence below pass threshold; manual verification recommended."
    return "PASS_NO_VISIBLE_ANOMALY", "No visible anomaly detected. This is not a guarantee of food safety."


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
        image_bytes = b""
        ocr = OcrExtraction()
    decoded = decode_barcodes(image_bytes) if image_bytes and not barcode_code else []
    if decoded:
        ocr.barcode = decoded[0]
        ocr.field_status["barcode_code"] = "detected"
        if "barcode" not in ocr.fields:
            ocr.fields.append("barcode")

    if ocr.label_confidence < 0.7:
        ocr.product_name = None
        ocr.brand = None
        ocr.field_status.pop("product_name", None)
        ocr.field_status.pop("brand", None)

    # Values typed by the inspector override OCR; record where each value came from.
    field_status = dict(ocr.field_status)
    for name, value in (
        ("barcode_code", barcode_code), ("batch_number", batch_number), ("production_date", production_date),
        ("expiry_date", expiry_date), ("product_name", product_name), ("brand", brand),
    ):
        if value is not None and value != "":
            field_status[name] = "entered"
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
    scan_product_name = product_name or (product.name if product else None) or ai_result.product_name
    if not product_name and scan_product_name:
        # Barcode database names are identified; AI-only names are a visual guess.
        field_status["product_name"] = "detected" if product and scan_product_name == product.name else "needs_verification"
    if not brand and product and product.manufacturer:
        brand = product.manufacturer.name
        field_status["brand"] = "detected"
    ocr_expiry = expiry_date or (barcode_obj.expiry_date if barcode_obj else None)
    discrepancy_reason = _discrepancy_reason(
        ai_result.condition, ocr_expiry, production_date, raw_text=ocr.raw_text
    )

    overall, overall_reason = _overall_result(
        ai_result, ocr, barcode_code, expiry_date, discrepancy_reason, product_category,
        expiry_unverified=field_status.get("expiry_date") == "needs_verification",
    )
    ai_result.findings = [f"Overall result: {overall.replace('_', ' ')} - {overall_reason}"] + list(ai_result.findings or [])

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
        brand=brand,
        packaging_condition=_packaging_condition_from_ai(ai_result),
        label_confidence=ocr.label_confidence,
        detected_fields=",".join(ocr.fields),
        overall_result=overall,
        overall_reason=overall_reason,
        ocr_raw_text=ocr.raw_text or "",
        date_details=json.dumps(ocr.date_candidates),
        field_status=json.dumps(field_status),
        review_status="awaiting_review" if overall in ATTENTION_RESULTS else "not_required",
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

    log_event(
        action="scan_created",
        user_id=user.id,
        resource_type="scan",
        resource_id=str(scan.id),
        details=f"condition={scan.condition.value}, confidence={scan.confidence}, product={scan.product_name}",
    )
    return scan


def _scan_query_for_user(db: Session, user: User):
    return scan_query_for_user(db, user)


@router.get("/", response_model=List[ScanRead])
def list_scans(
    response: Response,
    limit: int = 100,
    offset: int = 0,
    filters: InspectionFilters = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    q = apply_filters(_scan_query_for_user(db, user), filters)
    response.headers["X-Total-Count"] = str(q.count())
    return q.order_by(Scan.created_at.desc()).offset(offset).limit(min(limit, 500)).all()


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    scan = get_scan_for_user(db, user, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/{scan_id}/detail", response_model=ScanDetail)
def get_scan_detail(scan_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Inspection record with its full audit trail (corrections, reviews, sign-offs)."""
    scan = get_scan_for_user(db, user, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/{scan_id}/image")
def get_scan_image(scan_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Evidence photo for an inspection (own organisation only)."""
    scan = get_scan_for_user(db, user, scan_id)
    if not scan or not scan.image_path or not os.path.isfile(scan.image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(scan.image_path)


_DATE_FIELDS = {"production_date", "expiry_date"}


def _parse_correction_value(field: str, value: Optional[str]):
    if value is None or not value.strip():
        return None
    value = value.strip()
    if field in _DATE_FIELDS:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
        raise HTTPException(status_code=422, detail=f"{field}: use YYYY-MM-DD or DD/MM/YYYY")
    if field == "category":
        try:
            return ProductCategory(value.lower())
        except ValueError:
            raise HTTPException(status_code=422, detail=f"category: must be one of {[c.value for c in ProductCategory]}")
    return value


def _as_text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    return v.value if hasattr(v, "value") else str(v)


@router.post("/{scan_id}/corrections", response_model=ScanDetail)
def correct_scan_field(
    scan_id: str,
    payload: ScanCorrectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Correct one field; the original value and OCR text are kept in the audit trail."""
    scan = get_scan_for_user(db, user, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.signed_off_at and user.role.value not in {"administrator", "company_admin"}:
        raise HTTPException(status_code=409, detail="Inspection is signed off; only an organisation admin can correct it")
    new_value = _parse_correction_value(payload.field, payload.value)
    original = getattr(scan, payload.field)
    if _as_text(original) == _as_text(new_value):
        raise HTTPException(status_code=422, detail="New value is the same as the current value")

    db.add(ScanCorrection(
        id=uuid.uuid4(), scan_id=scan.id, user_id=user.id, field=payload.field,
        original_value=_as_text(original), new_value=_as_text(new_value), reason=payload.reason.strip(),
    ))
    setattr(scan, payload.field, new_value)
    status_map = scan.field_status_map
    status_map[payload.field] = "corrected"
    scan.field_status = json.dumps(status_map)
    if scan.review_status == "not_required":
        scan.review_status = "awaiting_review"
    db.commit()
    db.refresh(scan)
    log_event(
        action="scan_corrected", user_id=user.id, resource_type="scan", resource_id=str(scan.id),
        details=f"field={payload.field}, from={_as_text(original)!r}, to={_as_text(new_value)!r}, reason={payload.reason.strip()!r}",
    )
    return scan


@router.post("/{scan_id}/signoff", response_model=ScanDetail)
def sign_off_scan(
    scan_id: str,
    payload: SignoffCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Record the inspector's final decision with an electronic acknowledgement."""
    scan = get_scan_for_user(db, user, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if not payload.acknowledged:
        raise HTTPException(status_code=422, detail="acknowledged: you must confirm the acknowledgement statement")
    if payload.typed_name.strip().lower() != (user.full_name or "").strip().lower():
        raise HTTPException(status_code=422, detail="typed_name: type your full name exactly as on your account")

    system_result = scan.overall_result
    if payload.decision == "confirm":
        if payload.final_result and payload.final_result != system_result:
            raise HTTPException(status_code=422, detail="final_result differs from the system result; use decision=override")
        final_result = system_result
    elif payload.decision == "override":
        if not payload.final_result or payload.final_result == system_result:
            raise HTTPException(status_code=422, detail="final_result: choose a result different from the system result")
        if not payload.override_reason or len(payload.override_reason.strip()) < 5:
            raise HTTPException(status_code=422, detail="override_reason: explain why the result is overridden")
        final_result = payload.final_result
    else:
        final_result = None

    signoff = InspectionSignoff(
        id=uuid.uuid4(), scan_id=scan.id, user_id=user.id, full_name=user.full_name,
        typed_name=payload.typed_name.strip(), email=user.email, role=user.role.value,
        decision=payload.decision, system_result=system_result, final_result=final_result,
        comments=payload.comments, override_reason=payload.override_reason,
        acknowledgement_text=ACKNOWLEDGEMENT_TEXT,
    )
    db.add(signoff)
    db.flush()
    scan.final_decision = payload.decision
    scan.final_result = final_result
    scan.signed_off_at = signoff.created_at or datetime.utcnow()
    scan.signed_off_by = user.id
    scan.review_status = "escalated" if payload.decision == "escalate" else "confirmed"
    db.commit()
    db.refresh(scan)
    log_event(
        action=f"scan_signoff_{payload.decision}", user_id=user.id, resource_type="scan", resource_id=str(scan.id),
        details=f"system_result={system_result}, final_result={final_result}",
    )
    return scan


@router.post("/{scan_id}/feedback", response_model=ScanRead)
def feedback(
    scan_id: str,
    payload: ScanFeedbackPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    scan = get_scan_for_user(db, user, scan_id)
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
