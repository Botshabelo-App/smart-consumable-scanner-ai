# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Scan
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import Condition, DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), user=Depends(require_user)):
    total = db.query(Scan).count()
    fresh = db.query(Scan).filter(Scan.condition == Condition.FRESH).count()
    near = db.query(Scan).filter(Scan.condition == Condition.NEAR_EXPIRY).count()
    expired = db.query(Scan).filter(Scan.condition == Condition.EXPIRED).count()
    suspicious = db.query(Scan).filter(Scan.condition == Condition.SUSPICIOUS).count()
    avg_confidence = db.query(func.avg(Scan.confidence)).scalar() or 0.0
    return DashboardStats(
        total_scanned=total,
        fresh=fresh,
        near_expiry=near,
        expired=expired,
        suspicious=suspicious,
        reports_generated=0,  # computed separately if needed
        average_confidence=float(avg_confidence),
    )
