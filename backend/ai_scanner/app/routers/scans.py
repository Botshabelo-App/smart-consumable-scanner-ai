import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Barcode, Product, Scan, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.limiter import limiter
from ai_scanner.app.schemas import Condition, ProductCategory, ScanFeedbackPayload, ScanRead, ScanResult
from ai_scanner.app.services.ai_client import AIAnalysisError, ai_client
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.openfoodfacts import lookup_barcode as openfoodfacts_lookup
from ai_scanner.app.services.report_service import save_upload

router = APIRouter()


def _resolve_product_from_barcode(db: Session, code: str):
    barcode = db.query(Barcode).filter(Barcode.code == code).first()
    if not barcode:
        external = openfoodfacts_lookup(code)
        if external:
            product = db.query(Product).filter(Product.name.ilike(external["name"] or "")).first()
            if not product:
                product = Product(
                    name=external["name"] or "Unknown product",
                    category=None,
                    packaging_type=external.get("packaging"),
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


def _discrepancy_reason(ai_condition: Condition, expiry_date: Optional[datetime]) -> Optional[str]:
    if expiry_date and expiry_date > datetime.utcnow() and ai_condition == Condition.EXPIRED:
        return "AI detected expired appearance but printed expiry date is in the future; flagged for review."
    if expiry_date and expiry_date <= datetime.utcnow() and ai_condition == Condition.FRESH:
        return "AI detected fresh appearance but printed expiry date has passed; flagged for review."
    return None


@router.post("/analyze", response_model=ScanRead)
@limiter.limit("30/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
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
    barcode_obj = _resolve_product_from_barcode(db, barcode_code) if barcode_code else None
    product_id = barcode_obj.product_id if barcode_obj else None
    product = db.query(Product).filter(Product.id == product_id).first() if product_id else None

    hint = product_name or (product.name if product else None) or barcode_code
    try:
        ai_result: ScanResult = await ai_client.analyze_image(image, product_hint=hint)
    except AIAnalysisError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

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

    scan_product_name = ai_result.product_name or product_name or (product.name if product else None)
    discrepancy_reason = _discrepancy_reason(ai_result.condition, expiry_date or (barcode_obj.expiry_date if barcode_obj else None))

    scan = Scan(
        id=uuid.uuid4(),
        product_id=product_id,
        barcode_id=barcode_obj.id if barcode_obj else None,
        company_id=company_id,
        branch_id=branch_id,
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

    log_event(
        action="scan_created",
        user_id=user.id,
        resource_type="scan",
        resource_id=str(scan.id),
        details=f"condition={scan.condition.value}, confidence={scan.confidence}, product={scan.product_name}",
    )
    return scan


@router.get("/", response_model=List[ScanRead])
def list_scans(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return db.query(Scan).order_by(Scan.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/{scan_id}/feedback", response_model=ScanRead)
def submit_scan_feedback(
    scan_id: str,
    payload: ScanFeedbackPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Inspector accepts or overrides an AI assessment and records the reason."""
    scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan.inspector_accepted = payload.accepted
    if not payload.accepted:
        scan.override_condition = payload.override_condition.value if payload.override_condition else None
        scan.override_reason = payload.reason
        scan.override_notes = payload.additional_notes
    else:
        scan.override_condition = None
        scan.override_reason = None
        scan.override_notes = None

    db.commit()
    db.refresh(scan)

    action = "scan_accepted" if payload.accepted else "scan_overridden"
    details = f"accepted={payload.accepted}"
    if not payload.accepted:
        details += f", override_condition={scan.override_condition}, reason={scan.override_reason}"
    log_event(
        action=action,
        user_id=user.id,
        resource_type="scan",
        resource_id=scan_id,
        details=details,
    )
    return scan
