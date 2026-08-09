# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Scan, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import Condition, DashboardStats

router = APIRouter()


def _is_admin(user: User) -> bool:
    return user.role.value in {"administrator", "company_admin"}


def _scan_query_for_user(db: Session, user: User):
    q = db.query(Scan)
    if not _is_admin(user) and user.company_id:
        q = q.filter(Scan.company_id == user.company_id)
    return q


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(require_user)):
    q = _scan_query_for_user(db, user)
    total = q.count()
    fresh = q.filter(Scan.condition == Condition.FRESH).count()
    near = q.filter(Scan.condition == Condition.NEAR_EXPIRY).count()
    expired = q.filter(Scan.condition == Condition.EXPIRED).count()
    suspicious = q.filter(Scan.condition == Condition.SUSPICIOUS).count()
    avg_confidence = q.with_entities(func.avg(Scan.confidence)).scalar() or 0.0
    return DashboardStats(
        total_scanned=total,
        fresh=fresh,
        near_expiry=near,
        expired=expired,
        suspicious=suspicious,
        reports_generated=0,  # computed separately if needed
        average_confidence=float(avg_confidence),
    )
