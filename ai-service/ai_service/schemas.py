# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Condition(str, Enum):
    FRESH = "fresh"
    NEAR_EXPIRY = "near_expiry"
    SUSPICIOUS = "suspicious"
    EXPIRED = "expired"


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


class ScanResult(BaseModel):
    condition: Condition
    confidence: float = Field(..., ge=0.0, le=1.0)
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    packaging_type: Optional[str] = None
    findings: List[str] = []
    expiry_risk: Optional[str] = None
