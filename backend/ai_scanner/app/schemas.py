from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserRole(str, Enum):
    GOVERNMENT_INSPECTOR = "government_inspector"
    MUNICIPAL_HEALTH_INSPECTOR = "municipal_health_inspector"
    SCHOOL_FOOD_INSPECTOR = "school_food_inspector"
    RESTAURANT_MANAGER = "restaurant_manager"
    WAREHOUSE_INSPECTOR = "warehouse_inspector"
    MANUFACTURER_QUALITY_INSPECTOR = "manufacturer_quality_inspector"
    SUPERMARKET_MANAGER = "supermarket_manager"
    WHOLESALER = "wholesaler"
    ADMINISTRATOR = "administrator"
    CONSUMER = "consumer"
    COMPANY_ADMIN = "company_admin"


class ProductCategory(str, Enum):
    FOOD = "food"
    MEAT = "meat"
    DAIRY = "dairy"
    SEAFOOD = "seafood"
    PRODUCE = "produce"
    BEVERAGE = "beverage"
    PACKAGED = "packaged"
    FROZEN = "frozen"
    DRY = "dry"
    OTHER = "other"


class Condition(str, Enum):
    FRESH = "fresh"
    NEAR_EXPIRY = "near_expiry"
    SUSPICIOUS = "suspicious"
    EXPIRED = "expired"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole
    organization: Optional[str] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        from ai_scanner.app.dependencies import validate_password

        try:
            validate_password(v)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    organization: Optional[str] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class ScanCreate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    barcode_code: Optional[str] = None
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    device_id: Optional[UUID] = None


class ScanResult(BaseModel):
    condition: Condition
    confidence: float = Field(..., ge=0.0, le=1.0)
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    packaging_type: Optional[str] = None
    findings: List[str] = []
    expiry_risk: Optional[str] = None


class ScanRead(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    barcode_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    condition: Condition
    confidence: float
    packaging_type: Optional[str] = None
    findings: List[str] = []
    expiry_risk: Optional[str] = None
    barcode_code: Optional[str] = None
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    ai_vs_label_discrepancy: bool = False
    discrepancy_reason: Optional[str] = None
    image_path: Optional[str] = None
    inspector_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    # Phase 6 feedback
    inspector_accepted: Optional[bool] = None
    override_condition: Optional[Condition] = None
    override_reason: Optional[str] = None
    override_notes: Optional[str] = None
    override_image_paths: List[str] = []

    @field_validator("findings", mode="before")
    @classmethod
    def _split_findings(cls, v):
        if isinstance(v, str):
            return [line for line in v.split("\n") if line]
        return v or []

    @field_validator("override_image_paths", mode="before")
    @classmethod
    def _split_override_images(cls, v):
        if isinstance(v, str):
            return [line for line in v.split("\n") if line]
        return v or []

    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    scan_id: UUID
    notes: Optional[str] = None
    include_signature: bool = False
    signature_data: Optional[str] = None


class ReportRead(BaseModel):
    id: UUID
    scan_id: UUID
    report_id: str
    notes: Optional[str]
    file_url: Optional[str]
    generated_at: datetime
    inspector_name: Optional[str]
    signature_data: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_scanned: int
    fresh: int
    near_expiry: int
    expired: int
    suspicious: int
    reports_generated: int
    average_confidence: float


class CategoryExpiryStat(BaseModel):
    category: ProductCategory
    expired: int
    near_expiry: int
    suspicious: int
    fresh: int


class ManufacturerTrend(BaseModel):
    manufacturer_name: str
    scan_count: int
    expired_count: int
    suspicious_count: int


class TimeSeriesPoint(BaseModel):
    bucket: str
    count: int
    average_confidence: float


class AnalyticsResult(BaseModel):
    stats: DashboardStats
    category_expiry: List[CategoryExpiryStat]
    manufacturer_trends: List[ManufacturerTrend]
    time_series: List[TimeSeriesPoint]
    geographic_distribution: List[dict]


class AuditLogRead(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Enterprise schemas

class CompanyCreate(BaseModel):
    name: str
    registration_number: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class CompanyRead(BaseModel):
    id: UUID
    name: str
    registration_number: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BranchCreate(BaseModel):
    company_id: UUID
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    manager_id: Optional[UUID] = None


class BranchRead(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    manager_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    branch_id: Optional[UUID] = None
    name: str
    platform: Optional[str] = None
    serial_identifier: Optional[str] = None


class DeviceRead(BaseModel):
    id: UUID
    branch_id: Optional[UUID] = None
    name: str
    platform: Optional[str] = None
    serial_identifier: Optional[str] = None
    registered_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ManufacturerCreate(BaseModel):
    name: str
    country: Optional[str] = None
    website: Optional[str] = None


class ManufacturerRead(BaseModel):
    id: UUID
    name: str
    country: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    company_id: Optional[UUID] = None
    manufacturer_id: Optional[UUID] = None
    name: str
    category: Optional[ProductCategory] = None
    packaging_type: Optional[str] = None
    default_shelf_life_days: Optional[int] = None


class ProductRead(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    manufacturer_id: Optional[UUID] = None
    name: str
    category: Optional[ProductCategory] = None
    packaging_type: Optional[str] = None
    default_shelf_life_days: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BarcodeCreate(BaseModel):
    product_id: Optional[UUID] = None
    code: str
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class BarcodeRead(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    product_name: Optional[str] = None
    code: str
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewRequestCreate(BaseModel):
    scan_id: UUID
    suggested_condition: Optional[Condition] = None
    reviewer_notes: Optional[str] = None


class ReviewRequestUpdate(BaseModel):
    status: ReviewStatus
    approved_label: Optional[Condition] = None
    reviewer_notes: Optional[str] = None


class ReviewRequestRead(BaseModel):
    id: UUID
    scan_id: UUID
    user_id: Optional[UUID] = None
    suggested_condition: Optional[Condition] = None
    reviewer_notes: Optional[str] = None
    status: ReviewStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    approved_label: Optional[Condition] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Phase 6: pilot deployment & continuous learning


class OrganizationType(str, Enum):
    SCHOOL_CANTEEN = "school_canteen"
    SCHOOL_NUTRITION_PROGRAM = "school_nutrition_program"
    SUPERMARKET = "supermarket"
    WAREHOUSE = "warehouse"
    FOOD_MANUFACTURER = "food_manufacturer"
    WHOLESALER = "wholesaler"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    MUNICIPAL_HEALTH = "municipal_health"
    GOVERNMENT_INSPECTOR = "government_inspector"
    OTHER = "other"


class PilotProfileCreate(BaseModel):
    name: str
    organization_type: OrganizationType
    settings: Dict[str, Any] = {}
    branding: Dict[str, Any] = {}
    inspection_workflow: Dict[str, Any] = {}


class PilotProfileRead(BaseModel):
    id: UUID
    name: str
    organization_type: OrganizationType
    settings: Dict[str, Any]
    branding: Dict[str, Any]
    inspection_workflow: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScanFeedbackPayload(BaseModel):
    accepted: bool
    override_condition: Optional[Condition] = None
    reason: Optional[str] = None
    additional_notes: Optional[str] = None


class ModelDeploymentStatus(str, Enum):
    STAGING = "staging"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


class ModelRegistryCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    version: str
    dataset_version: str
    training_date: datetime
    validation_metrics: Dict[str, Any]
    supported_categories: List[str]
    artifact_path: str
    checksum: str
    status: ModelDeploymentStatus = ModelDeploymentStatus.STAGING


class ModelRegistryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    model_id: str
    version: str
    dataset_version: str
    training_date: datetime
    validation_metrics: Dict[str, Any]
    supported_categories: List[str]
    artifact_path: str
    checksum: str
    status: ModelDeploymentStatus
    deployed_at: Optional[datetime] = None
    created_at: datetime


class OperationalMetrics(BaseModel):
    inference_success_rate: float
    average_scan_time_ms: float
    average_confidence: float
    api_latency_p95_ms: float
    offline_sync_success_rate: float
    device_health_score: float
    crash_count_24h: int
    active_model_version: str
    total_scans_24h: int


class PilotSuccessMetrics(BaseModel):
    inspection_completion_rate: float
    ai_agreement_rate: float
    false_positive_rate: float
    false_negative_rate: float
    user_satisfaction_score: float
    average_inspection_time_ms: float
    report_generation_success_rate: float
    offline_sync_reliability: float
