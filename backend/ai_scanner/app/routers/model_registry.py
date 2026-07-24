# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import json
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import ModelRegistry
from ai_scanner.app.dependencies import require_role, require_user
from ai_scanner.app.schemas import ModelDeploymentStatus, ModelRegistryCreate, ModelRegistryRead
from ai_scanner.app.services.audit import log_event

router = APIRouter()


def _model_read(model: ModelRegistry) -> ModelRegistryRead:
    return ModelRegistryRead(
        id=model.id,
        model_id=model.model_id,
        version=model.version,
        dataset_version=model.dataset_version,
        training_date=model.training_date,
        validation_metrics=json.loads(model.validation_metrics or "{}"),
        supported_categories=json.loads(model.supported_categories or "[]"),
        artifact_path=model.artifact_path,
        checksum=model.checksum,
        status=ModelDeploymentStatus(model.status),
        deployed_at=model.deployed_at,
        created_at=model.created_at,
    )


@router.post("/", response_model=ModelRegistryRead)
def register_model(
    payload: ModelRegistryCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    existing = db.query(ModelRegistry).filter(ModelRegistry.model_id == payload.model_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Model ID already exists")
    model = ModelRegistry(
        model_id=payload.model_id,
        version=payload.version,
        dataset_version=payload.dataset_version,
        training_date=payload.training_date,
        validation_metrics=json.dumps(payload.validation_metrics),
        supported_categories=json.dumps(payload.supported_categories),
        artifact_path=payload.artifact_path,
        checksum=payload.checksum,
        status=payload.status.value,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    log_event(
        action="model_registered",
        user_id=user.id,
        resource_type="model_registry",
        resource_id=str(model.id),
        details=f"model_id={payload.model_id}, version={payload.version}",
    )
    return _model_read(model)


@router.get("/", response_model=List[ModelRegistryRead])
def list_models(
    status: ModelDeploymentStatus = None,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    q = db.query(ModelRegistry)
    if status:
        q = q.filter(ModelRegistry.status == status.value)
    return [_model_read(m) for m in q.order_by(ModelRegistry.created_at.desc()).all()]


@router.get("/active", response_model=ModelRegistryRead)
def get_active_model(
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.status == ModelDeploymentStatus.ACTIVE.value).first()
    if not model:
        raise HTTPException(status_code=404, detail="No active model found")
    return _model_read(model)


@router.post("/{model_id}/promote")
def promote_model(
    model_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    active = (
        db.query(ModelRegistry)
        .filter(ModelRegistry.status == ModelDeploymentStatus.ACTIVE.value)
        .order_by(ModelRegistry.deployed_at.desc())
        .first()
    )

    def _score(metrics: dict) -> float:
        # Prefer macro F1, fall back to accuracy, then to 0 if neither is present.
        return float(metrics.get("f1_macro") or metrics.get("f1") or metrics.get("accuracy") or 0.0)

    if active and not force:
        current_score = _score(json.loads(active.validation_metrics or "{}"))
        new_score = _score(json.loads(model.validation_metrics or "{}"))
        if new_score < current_score:
            raise HTTPException(
                status_code=400,
                detail=f"New model score ({new_score}) is lower than active model ({current_score}). "
                       "Use force=true to override or improve validation metrics.",
            )

    # Demote any currently active model
    db.query(ModelRegistry).filter(ModelRegistry.status == ModelDeploymentStatus.ACTIVE.value).update(
        {ModelRegistry.status: ModelDeploymentStatus.ARCHIVED.value}
    )
    model.status = ModelDeploymentStatus.ACTIVE.value
    model.deployed_at = datetime.now(timezone.utc)
    db.commit()
    log_event(
        action="model_promoted",
        user_id=user.id,
        resource_type="model_registry",
        resource_id=str(model.id),
        details=f"model_id={model_id}, version={model.version}",
    )
    return {"status": "promoted", "model_id": model_id, "version": model.version}


@router.post("/{model_id}/rollback")
def rollback_model(
    model_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("administrator")),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.status != ModelDeploymentStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Only the active model can be rolled back")
    model.status = ModelDeploymentStatus.ROLLED_BACK.value
    model.deployed_at = None
    db.commit()
    log_event(
        action="model_rolled_back",
        user_id=user.id,
        resource_type="model_registry",
        resource_id=str(model.id),
        details=f"model_id={model_id}, version={model.version}",
    )
    return {"status": "rolled_back", "model_id": model_id, "version": model.version}
