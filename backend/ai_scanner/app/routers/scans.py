import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ai_scanner.app.schemas import ProductCategory

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Scan, User
from ai_scanner.app.dependencies import get_current_user, require_user
from ai_scanner.app.schemas import ScanCreate, ScanRead, ScanResult
from ai_scanner.app.services.ai_client import ai_client
from ai_scanner.app.services.report_service import save_upload

router = APIRouter()


@router.post("/analyze", response_model=ScanRead)
async def analyze_image(
    image: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    ai_result: ScanResult = await ai_client.analyze_image(image, product_hint=product_name)
    product_category = None
    if ai_result.category:
        product_category = ai_result.category
    elif category:
        try:
            product_category = ProductCategory(category.lower())
        except ValueError:
            pass

    scan = Scan(
        id=uuid.uuid4(),
        product_name=ai_result.product_name or product_name,
        category=product_category,
        condition=ai_result.condition,
        confidence=ai_result.confidence,
        packaging_type=ai_result.packaging_type,
        findings="\n".join(ai_result.findings) if ai_result.findings else "",
        expiry_risk=ai_result.expiry_risk,
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
