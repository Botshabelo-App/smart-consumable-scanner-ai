import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from ai_scanner.app.db.database import Base
from ai_scanner.app.schemas import Condition, ProductCategory, ReviewStatus, UserRole


def utc_now():
    return datetime.now(timezone.utc)


class PilotProfile(Base):
    __tablename__ = "pilot_profiles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    organization_type = Column(String, nullable=False)
    settings = Column(Text, default="{}")
    branding = Column(Text, default="{}")
    inspection_workflow = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), onupdate=utc_now)

    companies = relationship("Company", back_populates="pilot_profile")


class Company(Base):
    __tablename__ = "companies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    registration_number = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    pilot_profile_id = Column(PGUUID(as_uuid=True), ForeignKey("pilot_profiles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    pilot_profile = relationship("PilotProfile", back_populates="companies")
    branches = relationship("Branch", back_populates="company")
    users = relationship("User", back_populates="company", foreign_keys="User.company_id")
    products = relationship("Product", back_populates="company")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    manager_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    company = relationship("Company", back_populates="branches")
    users = relationship("User", back_populates="branch", foreign_keys="User.branch_id")


class Device(Base):
    __tablename__ = "devices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    serial_identifier = Column(String, nullable=True, unique=True)
    registered_at = Column(DateTime(timezone=True), default=utc_now)
    is_active = Column(Boolean, default=True)


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=True)
    website = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    products = relationship("Product", back_populates="manufacturer")


class Product(Base):
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    manufacturer_id = Column(PGUUID(as_uuid=True), ForeignKey("manufacturers.id"), nullable=True)
    name = Column(String, nullable=False)
    category = Column(Enum(ProductCategory, name="product_category"), nullable=True)
    packaging_type = Column(String, nullable=True)
    default_shelf_life_days = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    company = relationship("Company", back_populates="products")
    manufacturer = relationship("Manufacturer", back_populates="products")
    barcodes = relationship("Barcode", back_populates="product")


class Barcode(Base):
    __tablename__ = "barcodes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    code = Column(String, nullable=False, unique=True)
    batch_number = Column(String, nullable=True)
    production_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, default="manual")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    product = relationship("Product", back_populates="barcodes")


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False)
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    branch_id = Column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    scans = relationship("Scan", back_populates="inspector")
    company = relationship("Company", back_populates="users", foreign_keys=[company_id])
    branch = relationship("Branch", back_populates="users", foreign_keys=[branch_id])


class Scan(Base):
    __tablename__ = "scans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    barcode_id = Column(PGUUID(as_uuid=True), ForeignKey("barcodes.id"), nullable=True)
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    branch_id = Column(PGUUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    device_id = Column(PGUUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)

    product_name = Column(String, nullable=True)
    category = Column(Enum(ProductCategory, name="product_category"), nullable=True)
    condition = Column(Enum(Condition, name="condition"), nullable=False)
    confidence = Column(Float, nullable=False)
    packaging_type = Column(String, nullable=True)
    findings = Column(Text, default="")
    expiry_risk = Column(String, nullable=True)

    barcode_code = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    production_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    ai_vs_label_discrepancy = Column(Boolean, default=False)
    discrepancy_reason = Column(Text, nullable=True)

    image_path = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Phase 6: inspector human-in-the-loop feedback
    inspector_accepted = Column(Boolean, nullable=True)
    override_condition = Column(String, nullable=True)
    override_reason = Column(Text, nullable=True)
    override_notes = Column(Text, nullable=True)
    override_image_paths = Column(Text, nullable=True)

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
    signature_data = Column(Text, nullable=True)

    scan = relationship("Scan")

    @property
    def inspector_name(self) -> str | None:
        return self.scan.inspector_name if self.scan else None


class ReviewRequest(Base):
    __tablename__ = "review_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(PGUUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    suggested_condition = Column(Enum(Condition, name="condition"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus, name="review_status"), default=ReviewStatus.PENDING)
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_label = Column(Enum(Condition, name="condition"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    scan = relationship("Scan", foreign_keys=[scan_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User")


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    training_date = Column(DateTime(timezone=True), nullable=False)
    validation_metrics = Column(Text, nullable=False)  # JSON
    supported_categories = Column(Text, nullable=False)  # JSON list
    artifact_path = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    status = Column(String, default="staging")  # staging, active, rolled_back, archived
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
