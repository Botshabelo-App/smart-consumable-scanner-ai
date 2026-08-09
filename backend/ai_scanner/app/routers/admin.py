# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Branch, Company, Device, User
from ai_scanner.app.dependencies import get_password_hash, require_admin, require_role, validate_password
from ai_scanner.app.schemas import BranchCreate, BranchRead, CompanyCreate, CompanyRead, DeviceCreate, DeviceRead, UserCreate, UserRead
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.user_service import create_user

router = APIRouter()


def _is_global_admin(user: User) -> bool:
    return user.role.value == "administrator"


def _can_manage_company(user: User, company_id: Optional[UUID]) -> bool:
    if _is_global_admin(user):
        return True
    if user.role.value == "company_admin" and user.company_id:
        return str(company_id) == str(user.company_id)
    return False


def _resolve_user_organization(db: Session, payload: UserCreate) -> str:
    if payload.organization:
        return payload.organization
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        return company.name if company else ""
    return ""


class PasswordResetPayload(BaseModel):
    new_password: str


class UserActivationPayload(BaseModel):
    is_active: bool


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), user=Depends(require_role("administrator"))):
    c = Company(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    log_event(action="company_created", user_id=user.id, resource_type="company", resource_id=str(c.id))
    return c


@router.get("/companies", response_model=List[CompanyRead])
def list_companies(db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Company)
    if not _is_global_admin(user) and user.company_id:
        q = q.filter(Company.id == user.company_id)
    return q.order_by(Company.name).all()


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: UUID, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    if not _can_manage_company(user, company_id):
        raise HTTPException(status_code=403, detail="Cannot access this organisation")
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return c


@router.post("/branches", response_model=BranchRead)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    if not _can_manage_company(user, payload.company_id):
        raise HTTPException(status_code=403, detail="Cannot create branches outside your organisation")
    b = Branch(**payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    log_event(action="branch_created", user_id=user.id, resource_type="branch", resource_id=str(b.id))
    return b


@router.get("/branches", response_model=List[BranchRead])
def list_branches(company_id: UUID = None, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Branch)
    if not _is_global_admin(user) and user.company_id:
        q = q.filter(Branch.company_id == user.company_id)
    elif company_id:
        q = q.filter(Branch.company_id == company_id)
    return q.order_by(Branch.name).all()


@router.post("/devices", response_model=DeviceRead)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    d = Device(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    log_event(action="device_created", user_id=user.id, resource_type="device", resource_id=str(d.id))
    return d


@router.get("/devices", response_model=List[DeviceRead])
def list_devices(branch_id: UUID = None, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Device)
    if not _is_global_admin(user) and user.company_id:
        q = q.join(Branch).filter(Branch.company_id == user.company_id)
    if branch_id:
        q = q.filter(Device.branch_id == branch_id)
    return q.order_by(Device.name).all()


@router.post("/inspectors", response_model=UserRead)
def create_inspector(payload: UserCreate, db: Session = Depends(get_db), admin=Depends(require_role("administrator", "company_admin"))):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if not _can_manage_company(admin, payload.company_id):
        raise HTTPException(status_code=403, detail="Cannot create users outside your organisation")

    payload.organization = _resolve_user_organization(db, payload)
    user = create_user(db, payload)
    log_event(action="user_created", user_id=admin.id, resource_type="user", resource_id=str(user.id))
    return user


@router.get("/inspectors", response_model=List[UserRead])
def list_inspectors(db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(User)
    if not _is_global_admin(user) and user.company_id:
        q = q.filter(User.company_id == user.company_id)
    return q.order_by(User.full_name).all()


@router.post("/users/{user_id}/reset-password", response_model=UserRead)
def reset_user_password(
    user_id: UUID,
    payload: PasswordResetPayload,
    db: Session = Depends(get_db),
    admin=Depends(require_role("administrator", "company_admin")),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_manage_company(admin, target.company_id):
        raise HTTPException(status_code=403, detail="Cannot manage users outside your organisation")
    try:
        validate_password(payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    target.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(target)
    log_event(action="password_reset_by_admin", user_id=admin.id, resource_type="user", resource_id=str(target.id))
    return target


@router.patch("/users/{user_id}/activation", response_model=UserRead)
def set_user_activation(
    user_id: UUID,
    payload: UserActivationPayload,
    db: Session = Depends(get_db),
    admin=Depends(require_role("administrator", "company_admin")),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_manage_company(admin, target.company_id):
        raise HTTPException(status_code=403, detail="Cannot manage users outside your organisation")
    target.is_active = payload.is_active
    db.commit()
    db.refresh(target)
    log_event(
        action="user_activated" if payload.is_active else "user_deactivated",
        user_id=admin.id,
        resource_type="user",
        resource_id=str(target.id),
    )
    return target
