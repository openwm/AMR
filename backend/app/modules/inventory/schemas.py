from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    uom: str = "EA"
    barcode: str | None = None
    category: str | None = None
    min_stock: int = 0
    unit_cost: Decimal = Decimal("0")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    uom: str | None = None
    barcode: str | None = None
    category: str | None = None
    min_stock: int | None = None
    unit_cost: Decimal | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    zone: str
    aisle: str | None = None
    rack: str | None = None
    bin: str | None = None
    type: str = "STORAGE"
    is_pickable: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    zone: str | None = None
    aisle: str | None = None
    rack: str | None = None
    bin: str | None = None
    type: str | None = None
    is_pickable: bool | None = None


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StockItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    location_id: int
    quantity: int
    lot_number: str
    expiry_date: date | None
    updated_at: datetime
    product_sku: str | None = None
    product_name: str | None = None
    location_code: str | None = None


class MovementCreate(BaseModel):
    product_id: int
    location_id: int
    quantity: int
    movement_type: str
    reference_type: str | None = None
    reference_id: int | None = None
    lot_number: str = ""
    note: str | None = None


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    location_id: int
    quantity: int
    movement_type: str
    reference_type: str | None
    reference_id: int | None
    lot_number: str
    note: str | None
    created_at: datetime
    product_sku: str | None = None
    product_name: str | None = None
    location_code: str | None = None
