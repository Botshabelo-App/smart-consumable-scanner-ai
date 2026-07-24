from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import ReviewRequest, Scan
from ai_scanner.app.dependencies import require_role, require_user
from ai_scanner.app.schemas import ReviewRequestCreate, ReviewRequestRead, ReviewRequestUpdate, ReviewStatus
from ai_scanner.app.services.audit import log_event

router = APIRouter()


@router.post("/", response_model=ReviewRequestRead)
def create_review_request(
    payload: ReviewRequestCreate,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    scan = db.query(Scan).filter(Scan.id == payload.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    r = ReviewRequest(
        scan_id=payload.scan_id,
        user_id=user.id,
        suggested_condition=payload.suggested_condition,
        reviewer_notes=payload.reviewer_notes,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    log_event(
        action="review_requested",
        user_id=user.id,
        resource_type="scan",
        resource_id=str(scan.id),
        details=f"suggested_condition={payload.suggested_condition}",
    )
    return r


@router.get("/", response_model=List[ReviewRequestRead])
def list_review_requests(
    status: ReviewStatus = None,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    q = db.query(ReviewRequest)
    if status:
        q = q.filter(ReviewRequest.status == status)
    return q.order_by(ReviewRequest.created_at.desc()).all()


@router.patch("/{review_id}", response_model=ReviewRequestRead)
def update_review_request(
    review_id: UUID,
    payload: ReviewRequestUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    r = db.query(ReviewRequest).filter(ReviewRequest.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review request not found")
    if payload.status:
        r.status = payload.status
    if payload.approved_label:
        r.approved_label = payload.approved_label
    if payload.reviewer_notes is not None:
        r.reviewer_notes = payload.reviewer_notes
    r.reviewed_by = user.id
    r.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    log_event(
        action=f"review_{payload.status.value}",
        user_id=user.id,
        resource_type="review_request",
        resource_id=str(r.id),
        details=f"approved_label={payload.approved_label}",
    )
    return r


@router.get("/export", response_model=List[dict])
def export_approved_reviews(
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    """Export approved review examples for offline retraining."""
    rows = (
        db.query(ReviewRequest, Scan)
        .join(Scan, ReviewRequest.scan_id == Scan.id)
        .filter(ReviewRequest.status == ReviewStatus.APPROVED)
        .all()
    )
    return [
        {
            "scan_id": str(scan.id),
            "image_path": scan.image_path,
            "product_name": scan.product_name,
            "category": scan.category.value if scan.category else None,
            "approved_condition": review.approved_label.value if review.approved_label else None,
            "suggested_condition": review.suggested_condition.value if review.suggested_condition else None,
            "reviewer_notes": review.reviewer_notes,
        }
        for review, scan in rows
    ]
