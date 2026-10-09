# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Branch, Scan, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import Condition, DashboardStats, DashboardSummary, InspectionFilters
from ai_scanner.app.services.inspection import apply_filters, scan_query_for_user

router = APIRouter()


def _is_admin(user: User) -> bool:
    """Only platform administrators see across organisations; company admins stay scoped."""
    return user.role.value == "administrator"


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


def _counts(q):
    row = q.with_entities(
        func.count(Scan.id),
        func.sum(case((Scan.overall_result == "PASS_NO_VISIBLE_ANOMALY", 1), else_=0)),
        func.sum(case((Scan.overall_result == "WARNING", 1), else_=0)),
        func.sum(case((Scan.overall_result == "REVIEW", 1), else_=0)),
    ).one()
    return {"total": row[0] or 0, "pass": int(row[1] or 0), "warning": int(row[2] or 0), "review": int(row[3] or 0)}


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    filters: InspectionFilters = Depends(),
    tz: str = Query("Africa/Johannesburg"),
    days: int = Query(30, ge=1, le=366),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Inspection counts computed live from the organisation's records."""
    try:
        zone = ZoneInfo(tz)
    except Exception:
        zone = ZoneInfo("Africa/Johannesburg")
    q = apply_filters(scan_query_for_user(db, user), filters)
    now = datetime.now(timezone.utc)
    local_midnight = datetime.now(zone).replace(hour=0, minute=0, second=0, microsecond=0)

    c = _counts(q)
    recent = q.order_by(Scan.created_at.desc()).limit(10).all()

    by_site = []
    for branch_id, *_ in q.with_entities(Scan.branch_id).distinct().all():
        name = db.query(Branch.name).filter(Branch.id == branch_id).scalar() if branch_id else None
        by_site.append({"branch_id": str(branch_id) if branch_id else None, "site": name or "No site assigned",
                        **_counts(q.filter(Scan.branch_id == branch_id) if branch_id else q.filter(Scan.branch_id.is_(None)))})
    by_inspector = []
    for inspector_id, *_ in q.with_entities(Scan.inspector_id).distinct().all():
        u = db.query(User).filter(User.id == inspector_id).first() if inspector_id else None
        by_inspector.append({"inspector_id": str(inspector_id) if inspector_id else None,
                             "inspector": u.full_name if u else "Unknown",
                             **_counts(q.filter(Scan.inspector_id == inspector_id))})

    day = func.date(func.timezone(tz if zone.key == tz else "Africa/Johannesburg", Scan.created_at))
    trend_rows = (
        q.filter(Scan.created_at >= now - timedelta(days=days))
        .with_entities(
            day, func.count(Scan.id),
            func.sum(case((Scan.overall_result == "PASS_NO_VISIBLE_ANOMALY", 1), else_=0)),
            func.sum(case((Scan.overall_result == "WARNING", 1), else_=0)),
            func.sum(case((Scan.overall_result == "REVIEW", 1), else_=0)),
        )
        .group_by(day).order_by(day).all()
    )
    return DashboardSummary(
        total=c["total"],
        today=q.filter(Scan.created_at >= local_midnight).count(),
        pass_count=c["pass"],
        warning=c["warning"],
        review=c["review"],
        insufficient_data=q.filter(Scan.overall_result == "INSUFFICIENT_DATA").count(),
        expired_products=q.filter(Scan.expiry_date < now).count(),
        awaiting_review=q.filter(Scan.review_status.in_(["awaiting_review", "escalated"])).count(),
        signed_off=q.filter(Scan.signed_off_at.isnot(None)).count(),
        recent=[{
            "id": str(s.id), "product_name": s.product_name, "brand": s.brand, "overall_result": s.overall_result,
            "review_status": s.review_status, "inspector": s.inspector_name, "site": s.branch_name,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in recent],
        by_site=by_site,
        by_inspector=by_inspector,
        trend=[{"date": d.isoformat(), "total": t, "pass": int(p or 0), "warning": int(w or 0), "review": int(r or 0)}
               for d, t, p, w, r in trend_rows],
        filters={k: (str(v) if v is not None else None) for k, v in filters.model_dump().items()},
    )
