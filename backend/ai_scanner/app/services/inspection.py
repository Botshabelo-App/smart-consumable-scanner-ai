# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Shared inspection-record helpers: tenant scoping, filters and sign-off wording."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from ai_scanner.app.db.models import Scan, User
from ai_scanner.app.schemas import InspectionFilters

ACKNOWLEDGEMENT_TEXT = (
    "I confirm that I personally inspected this product and that this record, including any "
    "corrections, is accurate to the best of my knowledge. This is an electronic acknowledgement "
    "linked to my authenticated account and timestamp; it is not a certified digital signature."
)

ATTENTION_RESULTS = {"WARNING", "REVIEW", "INSUFFICIENT_DATA"}


def is_global_admin(user: User) -> bool:
    """Only platform administrators see across organisations."""
    return user.role.value == "administrator"


def scan_query_for_user(db: Session, user: User) -> Query:
    q = db.query(Scan)
    if not is_global_admin(user):
        q = q.filter(Scan.company_id == user.company_id) if user.company_id else q.filter(Scan.inspector_id == user.id)
    return q


def get_scan_for_user(db: Session, user: User, scan_id) -> Optional[Scan]:
    try:
        sid = scan_id if isinstance(scan_id, uuid.UUID) else uuid.UUID(str(scan_id))
    except ValueError:
        return None
    return scan_query_for_user(db, user).filter(Scan.id == sid).first()


def apply_filters(q: Query, f: InspectionFilters) -> Query:
    if f.date_from:
        q = q.filter(Scan.created_at >= f.date_from)
    if f.date_to:
        # A bare date means "up to the end of that day".
        end = f.date_to + timedelta(days=1) if f.date_to.time() == datetime.min.time() else f.date_to
        q = q.filter(Scan.created_at < end)
    if f.branch_id:
        q = q.filter(Scan.branch_id == f.branch_id)
    if f.inspector_id:
        q = q.filter(Scan.inspector_id == f.inspector_id)
    if f.result:
        q = q.filter(Scan.overall_result == f.result)
    if f.review_status:
        q = q.filter(Scan.review_status == f.review_status)
    if f.product and f.product.strip():
        like = f"%{f.product.strip()}%"
        q = q.filter(or_(
            Scan.product_name.ilike(like), Scan.brand.ilike(like),
            Scan.barcode_code.ilike(like), Scan.batch_number.ilike(like),
        ))
    return q
