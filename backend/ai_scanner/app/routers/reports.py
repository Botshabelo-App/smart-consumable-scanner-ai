# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import json
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Company, Report, Scan, User
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import BatchReportCreate, ReportCreate, ReportRead
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.inspection import apply_filters, scan_query_for_user
from ai_scanner.app.services.report_service import generate_batch, generate_csv, generate_excel, generate_pdf

router = APIRouter()


def _is_admin(user: User) -> bool:
    """Only platform administrators see across organisations; company admins stay scoped."""
    return user.role.value == "administrator"


def _scan_query_for_user(db: Session, user: User):
    return scan_query_for_user(db, user)


def _report_query_for_user(db: Session, user: User):
    q = db.query(Report).outerjoin(Scan, Report.scan_id == Scan.id)
    if not _is_admin(user):
        if user.company_id:
            q = q.filter(or_(Scan.company_id == user.company_id, Report.company_id == user.company_id))
        else:
            q = q.filter(Report.created_by == user.id)
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
        company_id=scan.company_id,
        created_by=user.id,
        report_type="single",
        format=format,
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


@router.post("/batch", response_model=ReportRead)
def create_batch_report(
    payload: BatchReportCreate,
    format: str = Query("pdf", pattern="^(pdf|csv|excel)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """One report covering every inspection that matches the filters (own organisation only)."""
    scans = (
        apply_filters(_scan_query_for_user(db, user), payload)
        .order_by(Scan.created_at.desc())
        .limit(payload.limit)
        .all()
    )
    filters = {k: (str(v) if v is not None else None) for k, v in payload.model_dump(exclude={"notes", "limit"}).items()}
    report = Report(
        id=uuid.uuid4(),
        report_id=_new_report_id(),
        scan_id=None,
        notes=payload.notes,
        company_id=user.company_id,
        created_by=user.id,
        report_type="batch",
        format=format,
        filters=json.dumps(filters),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    company = db.query(Company).filter(Company.id == user.company_id).first() if user.company_id else None
    report.file_url = generate_batch(scans, report, format, user.full_name, filters, company.name if company else "All organisations")
    db.commit()
    db.refresh(report)
    log_event(
        action="report_generated",
        user_id=user.id,
        resource_type="report",
        resource_id=str(report.id),
        details=f"type=batch, format={format}, report_id={report.report_id}, inspections={len(scans)}, filters={filters}",
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


