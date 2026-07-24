from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole
    organization: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    organization: Optional[str] = None
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
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    condition: Condition
    confidence: float
    image_path: Optional[str] = None
    inspector_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    scan_id: UUID
    notes: Optional[str] = None
    include_signature: bool = False


class ReportRead(BaseModel):
    id: UUID
    scan_id: UUID
    report_id: str
    notes: Optional[str]
    file_url: Optional[str]
    generated_at: datetime
    inspector_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_scanned: int
    fresh: int
    near_expiry: int
    expired: int
    suspicious: int
    reports_generated: int
    average_confidence: float
