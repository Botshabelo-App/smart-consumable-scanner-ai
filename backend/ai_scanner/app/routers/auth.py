from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import User
from ai_scanner.app.dependencies import create_access_token, validate_password, verify_password
from ai_scanner.app.limiter import limiter
from ai_scanner.app.schemas import Token, UserCreate, UserLogin, UserRead
from ai_scanner.app.services.audit import log_event
from ai_scanner.app.services.user_service import create_user

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Password complexity is validated by the UserCreate schema; keep an explicit check here
    # so registration failures return a clear 400 before any DB write.
    try:
        validate_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    user = create_user(db, payload)
    log_event(action="user_register", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    log_event(action="user_login", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return Token(access_token=token, token_type="bearer")
