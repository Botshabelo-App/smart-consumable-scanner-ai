# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Company, PilotProfile
from ai_scanner.app.dependencies import require_role, require_user
from ai_scanner.app.schemas import OrganizationType, PilotProfileCreate, PilotProfileRead
from ai_scanner.app.services.audit import log_event

router = APIRouter()


def _profile_read(profile: PilotProfile) -> PilotProfileRead:
    return PilotProfileRead(
        id=profile.id,
        name=profile.name,
        organization_type=OrganizationType(profile.organization_type),
        settings=json.loads(profile.settings or "{}"),
        branding=json.loads(profile.branding or "{}"),
        inspection_workflow=json.loads(profile.inspection_workflow or "{}"),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post("/", response_model=PilotProfileRead)
def create_profile(
    payload: PilotProfileCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    profile = PilotProfile(
        name=payload.name,
        organization_type=payload.organization_type.value,
        settings=json.dumps(payload.settings),
        branding=json.dumps(payload.branding),
        inspection_workflow=json.dumps(payload.inspection_workflow),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    log_event(
        action="pilot_profile_created",
        user_id=user.id,
        resource_type="pilot_profile",
        resource_id=str(profile.id),
    )
    return _profile_read(profile)


@router.get("/", response_model=List[PilotProfileRead])
def list_profiles(
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    profiles = db.query(PilotProfile).order_by(PilotProfile.created_at.desc()).all()
    return [_profile_read(p) for p in profiles]


@router.get("/{profile_id}", response_model=PilotProfileRead)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    profile = db.query(PilotProfile).filter(PilotProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Pilot profile not found")
    return _profile_read(profile)


@router.put("/{profile_id}", response_model=PilotProfileRead)
def update_profile(
    profile_id: UUID,
    payload: PilotProfileCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    profile = db.query(PilotProfile).filter(PilotProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Pilot profile not found")
    profile.name = payload.name
    profile.organization_type = payload.organization_type.value
    profile.settings = json.dumps(payload.settings)
    profile.branding = json.dumps(payload.branding)
    profile.inspection_workflow = json.dumps(payload.inspection_workflow)
    db.commit()
    db.refresh(profile)
    log_event(
        action="pilot_profile_updated",
        user_id=user.id,
        resource_type="pilot_profile",
        resource_id=str(profile.id),
    )
    return _profile_read(profile)


@router.post("/{profile_id}/assign/{company_id}")
def assign_profile_to_company(
    profile_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    profile = db.query(PilotProfile).filter(PilotProfile.id == profile_id).first()
    company = db.query(Company).filter(Company.id == company_id).first()
    if not profile or not company:
        raise HTTPException(status_code=404, detail="Profile or company not found")
    company.pilot_profile_id = profile.id
    db.commit()
    log_event(
        action="pilot_profile_assigned",
        user_id=user.id,
        resource_type="company",
        resource_id=str(company.id),
        details=f"profile_id={profile_id}",
    )
    return {"status": "ok"}
