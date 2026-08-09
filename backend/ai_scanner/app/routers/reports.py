# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Report, Scan, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import ReportCreate, ReportRead
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.report_service import generate_csv, generate_excel, generate_pdf

router = APIRouter()


def _is_admin(user: User) -> bool:
    return user.role.value in {"administrator", "company_admin"}


def _scan_query_for_user(db: Session, user: User):
    q = db.query(Scan)
    if not _is_admin(user) and user.company_id:
        q = q.filter(Scan.company_id == user.company_id)
    return q


def _report_query_for_user(db: Session, user: User):
    q = db.query(Report).join(Scan)
    if not _is_admin(user) and user.company_id:
        q = q.filter(Scan.company_id == user.company_id)
    return q


def _new_report_id() -> str:
    return f"RPT-{uuid.uuid4().hex[:12].upper()}"


@router.post("/", response_model=ReportRead)
def create_report(
    payload: ReportCreate,
    format: str = Query("pdf", pattern="^(pdf|csv|excel)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    scan = _scan_query_for_user(db, user).filter(Scan.id == payload.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    report = Report(
        id=uuid.uuid4(),
        report_id=_new_report_id(),
        scan_id=scan.id,
        notes=payload.notes,
        signature_data=payload.signature_data if payload.include_signature else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    inspector_name = user.full_name
    if format == "pdf":
        file_path = generate_pdf(scan, report, inspector_name)
    elif format == "csv":
        file_path = generate_csv(scan, report, inspector_name)
    else:
        file_path = generate_excel(scan, report, inspector_name)

    report.file_url = file_path
    db.commit()
    db.refresh(report)

    log_event(
        action="report_generated",
        user_id=user.id,
        resource_type="report",
        resource_id=str(report.id),
        details=f"format={format}, report_id={report.report_id}",
    )
    return report


@router.get("/", response_model=List[ReportRead])
def list_reports(db: Session = Depends(get_db), user: User = Depends(require_user)):
    return (
        _report_query_for_user(db, user)
        .order_by(Report.generated_at.desc())
        .all()
    )


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        report_uuid = None
    q = _report_query_for_user(db, user)
    report = (
        q.filter(Report.id == report_uuid).first()
        if report_uuid else None
    ) or q.filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        report_uuid = None
    q = _report_query_for_user(db, user)
    report = (
        q.filter(Report.id == report_uuid).first()
        if report_uuid else None
    ) or q.filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_url or not os.path.exists(report.file_url):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(report.file_url, filename=os.path.basename(report.file_url))


