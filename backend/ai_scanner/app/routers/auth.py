# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Company, User
from ai_scanner.app.dependencies import create_access_token, get_password_hash, require_admin, require_user, validate_password, verify_password
from ai_scanner.app.limiter import limiter
from ai_scanner.app.schemas import OrganisationRead, OrganisationRegister, Token, UserCreate, UserLogin, UserRead
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.user_service import create_user
from ai_scanner.config import settings

router = APIRouter()


def _utc_now():
    return datetime.now(timezone.utc)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a user within an organisation (admin-only)."""
    if admin.role.value == "company_admin" and admin.company_id and payload.company_id != admin.company_id:
        raise HTTPException(status_code=403, detail="Cannot create users outside your organisation")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        validate_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not payload.organization and admin.company_id:
        company = db.query(Company).filter(Company.id == admin.company_id).first()
        payload.organization = company.name if company else None
    user = create_user(db, payload)
    log_event(action="user_register", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return user


@router.post("/register-organisation", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_organisation(request: Request, payload: OrganisationRegister, db: Session = Depends(get_db)):
    """Create a new organisation and its first administrator."""
    if db.query(User).filter(User.email == payload.admin_email).first():
        raise HTTPException(status_code=400, detail="Admin email already registered")

    company = Company(
        name=payload.organisation_name,
        registration_number=payload.registration_number,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )
    db.add(company)
    db.flush()  # obtain company.id

    try:
        validate_password(payload.admin_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    admin = User(
        email=payload.admin_email,
        full_name=payload.admin_full_name,
        hashed_password=get_password_hash(payload.admin_password),
        role="company_admin",
        organization=payload.organisation_name,
        company_id=company.id,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(company)
    db.refresh(admin)

    log_event(
        action="organisation_registered",
        user_id=admin.id,
        resource_type="company",
        resource_id=str(company.id),
        details=f"organisation={company.name}, admin={admin.email}",
    )

    return OrganisationRead(
        id=company.id,
        name=company.name,
        registration_number=company.registration_number,
        contact_email=company.contact_email,
        contact_phone=company.contact_phone,
        admin=UserRead.model_validate(admin),
        created_at=company.created_at,
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    token_payload = {
        "sub": str(user.id),
        "org": str(user.company_id) if user.company_id else None,
    }
    token = create_access_token(token_payload)
    log_event(action="user_login", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return Token(access_token=token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, user: User = Depends(require_user)):
    """JWT logout is client-side; the server records the event."""
    log_event(action="user_logout", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(require_user)):
    return user


@router.post("/password-reset-request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
def request_password_reset(request: Request, email: str, db: Session = Depends(get_db)):
    """Start a password reset. In production this sends an email; without SMTP it returns a token for testing."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"detail": "If the account exists, a reset link has been sent."}

    token = create_access_token(
        {"sub": str(user.id), "reset": True},
        expires_delta=timedelta(minutes=15),
    )
    log_event(action="password_reset_request", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return {"detail": "If the account exists, a reset link has been sent.", "reset_token": token}


@router.post("/reset-password", response_model=UserRead)
@limiter.limit("5/minute")
def reset_password(request: Request, token: str, new_password: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if not payload.get("reset"):
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user_id = payload.get("sub")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        validate_password(new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    log_event(action="password_reset", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return user
