from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Scan
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import (
    AnalyticsResult,
    CategoryExpiryStat,
    Condition,
    DashboardStats,
    ManufacturerTrend,
    ProductCategory,
    TimeSeriesPoint,
)

router = APIRouter()


def _series_for_range(start: datetime, end: datetime):
    # daily buckets for the last 30 days
    return [
        (start.date() + timedelta(days=i)).isoformat()
        for i in range((end.date() - start.date()).days + 1)
    ]


@router.get("/", response_model=AnalyticsResult)
def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    total = db.query(Scan).count()
    fresh = db.query(Scan).filter(Scan.condition == Condition.FRESH).count()
    near = db.query(Scan).filter(Scan.condition == Condition.NEAR_EXPIRY).count()
    expired = db.query(Scan).filter(Scan.condition == Condition.EXPIRED).count()
    suspicious = db.query(Scan).filter(Scan.condition == Condition.SUSPICIOUS).count()
    reports_generated = db.query(Scan).count()  # placeholder until report table join
    avg_confidence = db.query(func.avg(Scan.confidence)).scalar() or 0.0

    stats = DashboardStats(
        total_scanned=total,
        fresh=fresh,
        near_expiry=near,
        expired=expired,
        suspicious=suspicious,
        reports_generated=reports_generated,
        average_confidence=float(avg_confidence),
    )

    category_expiry: List[CategoryExpiryStat] = []
    for cat in ProductCategory:
        cat_fresh = db.query(Scan).filter(Scan.category == cat, Scan.condition == Condition.FRESH).count()
        cat_near = db.query(Scan).filter(Scan.category == cat, Scan.condition == Condition.NEAR_EXPIRY).count()
        cat_expired = db.query(Scan).filter(Scan.category == cat, Scan.condition == Condition.EXPIRED).count()
        cat_suspicious = db.query(Scan).filter(Scan.category == cat, Scan.condition == Condition.SUSPICIOUS).count()
        category_expiry.append(
            CategoryExpiryStat(
                category=cat,
                expired=cat_expired,
                near_expiry=cat_near,
                suspicious=cat_suspicious,
                fresh=cat_fresh,
            )
        )

    manufacturer_trends: List[ManufacturerTrend] = []
    manufacturer_query = (
        db.query(Scan.product_name, func.count(Scan.id), func.avg(Scan.confidence))
        .group_by(Scan.product_name)
        .all()
    )
    for name, count, avg in manufacturer_query[:10]:
        if not name:
            continue
        expired_count = db.query(Scan).filter(Scan.product_name == name, Scan.condition == Condition.EXPIRED).count()
        suspicious_count = db.query(Scan).filter(Scan.product_name == name, Scan.condition == Condition.SUSPICIOUS).count()
        manufacturer_trends.append(
            ManufacturerTrend(
                manufacturer_name=name,
                scan_count=count,
                expired_count=expired_count,
                suspicious_count=suspicious_count,
            )
        )

    time_series = []
    for bucket in _series_for_range(start, end):
        day = datetime.fromisoformat(bucket).date()
        rows = db.query(Scan).filter(func.date(Scan.created_at) == day)
        count = rows.count()
        avg_conf = db.query(func.avg(Scan.confidence)).filter(func.date(Scan.created_at) == day).scalar() or 0.0
        time_series.append(
            TimeSeriesPoint(bucket=bucket, count=count, average_confidence=float(avg_conf))
        )

    geo = (
        db.query(Scan.latitude, Scan.longitude, func.count(Scan.id))
        .filter(Scan.latitude.isnot(None), Scan.longitude.isnot(None))
        .group_by(Scan.latitude, Scan.longitude)
        .all()
    )
    geographic_distribution = [
        {"latitude": lat, "longitude": lng, "count": cnt} for lat, lng, cnt in geo
    ]

    return AnalyticsResult(
        stats=stats,
        category_expiry=category_expiry,
        manufacturer_trends=manufacturer_trends,
        time_series=time_series,
        geographic_distribution=geographic_distribution,
    )
