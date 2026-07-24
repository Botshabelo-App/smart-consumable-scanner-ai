from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Branch, Company, Device, User
from ai_scanner.app.dependencies import get_password_hash, require_role
from ai_scanner.app.schemas import BranchCreate, BranchRead, CompanyCreate, CompanyRead, DeviceCreate, DeviceRead, UserCreate, UserRead

router = APIRouter()


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    c = Company(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/companies", response_model=List[CompanyRead])
def list_companies(db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Company)
    if user.role.value == "company_admin" and user.company_id:
        q = q.filter(Company.id == user.company_id)
    return q.order_by(Company.name).all()


@router.post("/branches", response_model=BranchRead)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    if user.role.value == "company_admin" and user.company_id and payload.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Cannot create branches outside your company")
    b = Branch(**payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/branches", response_model=List[BranchRead])
def list_branches(company_id: UUID = None, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Branch)
    if user.role.value == "company_admin" and user.company_id:
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
    return d


@router.get("/devices", response_model=List[DeviceRead])
def list_devices(branch_id: UUID = None, db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(Device)
    if branch_id:
        q = q.filter(Device.branch_id == branch_id)
    return q.order_by(Device.name).all()


@router.post("/inspectors", response_model=UserRead)
def create_inspector(payload: UserCreate, db: Session = Depends(get_db), admin=Depends(require_role("administrator", "company_admin"))):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        organization=payload.organization,
        company_id=payload.company_id,
        branch_id=payload.branch_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/inspectors", response_model=List[UserRead])
def list_inspectors(db: Session = Depends(get_db), user=Depends(require_role("administrator", "company_admin"))):
    q = db.query(User)
    if user.role.value == "company_admin" and user.company_id:
        q = q.filter(User.company_id == user.company_id)
    return q.order_by(User.full_name).all()
