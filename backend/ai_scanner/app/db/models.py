import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from ai_scanner.app.db.database import Base
from ai_scanner.app.schemas import Condition, ProductCategory, UserRole


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    scans = relationship("Scan", back_populates="inspector")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name = Column(String, nullable=True)
    category = Column(Enum(ProductCategory, name="product_category"), nullable=True)
    condition = Column(Enum(Condition, name="condition"), nullable=False)
    confidence = Column(Float, nullable=False)
    packaging_type = Column(String, nullable=True)
    findings = Column(Text, default="")
    expiry_risk = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    inspector_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    inspector = relationship("User", back_populates="scans")

    @property
    def inspector_name(self) -> str | None:
        return self.inspector.full_name if self.inspector else None


class Report(Base):
    __tablename__ = "reports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String, unique=True, nullable=False)
    scan_id = Column(PGUUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    notes = Column(Text, nullable=True)
    file_url = Column(String, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utc_now)

    scan = relationship("Scan")

    @property
    def inspector_name(self) -> str | None:
        return self.scan.inspector_name if self.scan else None
