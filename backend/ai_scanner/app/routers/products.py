# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_scanner.app.db.database import get_db
from ai_scanner.app.db.models import Barcode, Manufacturer, Product
from ai_scanner.app.dependencies import require_user
from ai_scanner.app.schemas import BarcodeCreate, BarcodeRead, ManufacturerCreate, ManufacturerRead, ProductCreate, ProductRead
from ai_scanner.app.services.openfoodfacts import lookup_barcode

router = APIRouter()


@router.post("/manufacturers", response_model=ManufacturerRead)
def create_manufacturer(payload: ManufacturerCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    m = Manufacturer(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/manufacturers", response_model=List[ManufacturerRead])
def list_manufacturers(db: Session = Depends(get_db), user=Depends(require_user)):
    return db.query(Manufacturer).order_by(Manufacturer.name).all()


@router.post("/", response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    p = Product(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/", response_model=List[ProductRead])
def list_products(
    manufacturer_id: Optional[UUID] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    q = db.query(Product)
    if manufacturer_id:
        q = q.filter(Product.manufacturer_id == manufacturer_id)
    if category:
        q = q.filter(Product.category == category)
    return q.order_by(Product.name).all()


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: UUID, db: Session = Depends(get_db), user=Depends(require_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.post("/barcodes", response_model=BarcodeRead)
def create_barcode(payload: BarcodeCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    b = Barcode(**payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/barcodes/{code}", response_model=BarcodeRead)
def get_barcode(code: str, db: Session = Depends(get_db), user=Depends(require_user)):
    b = db.query(Barcode).filter(Barcode.code == code).first()
    if not b:
        data = lookup_barcode(code)
        if not data:
            raise HTTPException(status_code=404, detail="Barcode not found")
        manufacturer_name = data.get("brand") or data.get("manufacturer")
        manufacturer = (
            db.query(Manufacturer).filter(Manufacturer.name.ilike(manufacturer_name)).first()
            if manufacturer_name
            else None
        )
        if manufacturer_name and not manufacturer:
            manufacturer = Manufacturer(name=manufacturer_name, country=data.get("countries"))
            db.add(manufacturer)
            db.commit()
            db.refresh(manufacturer)
        product = Product(
            manufacturer_id=manufacturer.id if manufacturer else None,
            name=data.get("name", "Unknown product"),
            category=None,
            packaging_type=data.get("packaging"),
            default_shelf_life_days=None,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        b = Barcode(
            product_id=product.id,
            code=code,
            source="openfoodfacts",
        )
        db.add(b)
        db.commit()
        db.refresh(b)
    if b and b.product:
        b.product_name = b.product.name
    return b
