"""Shared user creation helper."""
from sqlalchemy.orm import Session

from ai_scanner.app.db.models import User
from ai_scanner.app.dependencies import get_password_hash
from ai_scanner.app.schemas import UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        organization=payload.organization,
        company_id=payload.company_id,
        branch_id=payload.branch_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
