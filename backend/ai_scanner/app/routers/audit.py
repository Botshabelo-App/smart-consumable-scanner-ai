from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import AuditLog, User
from ai_scanner.app.dependencies import require_role
from ai_scanner.app.schemas import AuditLogRead

router = APIRouter(prefix="/audit-logs")


@router.get("/", response_model=List[AuditLogRead])
def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("administrator")),
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
