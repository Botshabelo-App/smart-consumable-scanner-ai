# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Shared helpers for generating pilot monitoring reports."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ai_scanner.app.db.models import AuditLog, Company, ModelRegistry, ReviewRequest, Scan
from ai_scanner.app.schemas import ReviewStatus


def _period_label(start: datetime, end: datetime) -> str:
    return f"{start.date().isoformat()} to {end.date().isoformat()}"


def _count_scans(db: Session, start: Optional[datetime], end: Optional[datetime]) -> int:
    q = db.query(Scan)
    if start:
        q = q.filter(Scan.created_at >= start)
    if end:
        q = q.filter(Scan.created_at < end)
    return q.count()


def _count_feedback(db: Session, start: Optional[datetime], end: Optional[datetime]) -> tuple[int, int, int, int, int]:
    """Return total accepted, total overridden, FP, FN, and completed for the period."""
    base = db.query(Scan).filter(Scan.inspector_accepted.isnot(None))
    if start:
        base = base.filter(Scan.created_at >= start)
    if end:
        base = base.filter(Scan.created_at < end)

    accepted = base.filter(Scan.inspector_accepted == True).count()
    overridden = base.filter(Scan.inspector_accepted == False).count()
    completed = accepted + overridden

    fp = base.filter(
        Scan.inspector_accepted == False,
        Scan.override_condition.in_(["fresh", "near_expiry"]),
        Scan.condition.in_(["expired", "suspicious"]),
    ).count()
    fn = base.filter(
        Scan.inspector_accepted == False,
        Scan.override_condition.in_(["expired", "suspicious"]),
        Scan.condition.in_(["fresh", "near_expiry"]),
    ).count()
    return accepted, overridden, fp, fn, completed


def _crashes(db: Session, start: Optional[datetime], end: Optional[datetime]) -> int:
    q = db.query(AuditLog).filter(AuditLog.action == "client_crash")
    if start:
        q = q.filter(AuditLog.created_at >= start)
    if end:
        q = q.filter(AuditLog.created_at < end)
    return q.count()


def _active_model(db: Session) -> Optional[ModelRegistry]:
    return (
        db.query(ModelRegistry)
        .filter(ModelRegistry.status == "active")
        .order_by(ModelRegistry.deployed_at.desc())
        .first()
    )


def build_pilot_report(db: Session, start: datetime, end: datetime) -> str:
    period = _period_label(start, end)
    total_scans = _count_scans(db, start, end)
    accepted, overridden, fp, fn, completed = _count_feedback(db, start, end)
    agreement_rate = (accepted / completed) if completed else 0.0
    fp_rate = (fp / completed) if completed else 0.0
    fn_rate = (fn / completed) if completed else 0.0

    pending_reviews = db.query(ReviewRequest).filter(
        ReviewRequest.status == ReviewStatus.PENDING,
        ReviewRequest.created_at >= start,
        ReviewRequest.created_at < end,
    ).count()
    approved_reviews = db.query(ReviewRequest).filter(
        ReviewRequest.status == ReviewStatus.APPROVED,
        ReviewRequest.created_at >= start,
        ReviewRequest.created_at < end,
    ).count()

    crashes = _crashes(db, start, end)
    active_model = _active_model(db)
    companies = db.query(Company).count()

    lines = [
        f"# Pilot Monitoring Report — {period}",
        "",
        f"- **Period:** {period}",
        f"- **Total scans:** {total_scans}",
        f"- **Companies onboarded:** {companies}",
        "",
        "## AI Performance Summary",
        f"- **Inspector accepted:** {accepted}",
        f"- **Inspector overridden:** {overridden}",
        f"- **Completed inspections:** {completed}",
        f"- **AI agreement rate:** {agreement_rate:.2%}" if completed else "- **AI agreement rate:** N/A",
        f"- **False positives (AI over-flagged):** {fp} ({fp_rate:.2%})" if completed else "- **False positives:** N/A",
        f"- **False negatives (AI missed spoilage):** {fn} ({fn_rate:.2%})" if completed else "- **False negatives:** N/A",
        "",
        "## Review Queue",
        f"- **Pending reviews in period:** {pending_reviews}",
        f"- **Approved for retraining in period:** {approved_reviews}",
        "",
        "## Operational Health",
        f"- **Mobile crashes in period:** {crashes}",
        f"- **Active model:** {active_model.model_id}-{active_model.version}" if active_model else "- **Active model:** none registered",
        f"- **Active model dataset version:** {active_model.dataset_version}" if active_model else "",
        "",
        "## Recommended Actions",
        "1. Review all overrides with missing reasons.",
        "2. Resolve pending review requests within 48 hours.",
        "3. Investigate any false negatives before the next model retraining.",
        "4. Sync device logs and verify offline upload success rate.",
        "",
        "_Generated automatically by the Smart Consumable Scanner AI pilot reporting service._",
    ]
    return "\n".join(lines)


def build_weekly_report(db: Session) -> str:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    return build_pilot_report(db, start, end)


def build_monthly_report(db: Session) -> str:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    return build_pilot_report(db, start, end)
