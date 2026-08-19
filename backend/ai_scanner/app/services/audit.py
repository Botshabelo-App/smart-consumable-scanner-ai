# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ai_scanner.app.db.database import SessionLocal
from ai_scanner.app.db.models import AuditLog


def log_event(
    action: str,
    user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    db: Optional[Session] = None,
) -> None:
    close_db = db is None
    db = db or SessionLocal()
    try:
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
            )
        )
        db.commit()
    finally:
        if close_db:
            db.close()
