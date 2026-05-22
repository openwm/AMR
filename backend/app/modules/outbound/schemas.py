from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SOLineCreate(BaseModel):
    product_id: int
    qty_ordered: int = Field(..., gt=0)


class SOLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty_ordered: int
    qty_shipped: int


class SOCreate(BaseModel):
    reference: str
    customer: str
    requested_date: date | None = None
    notes: str | None = None
    lines: list[SOLineCreate]


class SORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    customer: str
    status: str
    requested_date: date | None
    notes: str | None
    created_at: datetime
    lines: list[SOLineRead]


class ShipmentLineCreate(BaseModel):
    so_line_id: int | None = None
    product_id: int
    location_id: int
    quantity: int = Field(..., gt=0)
    lot_number: str = ""


class ShipmentLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so_line_id: int | None
    product_id: int
    location_id: int
    quantity: int
    lot_number: str


class ShipmentCreate(BaseModel):
    reference: str
    so_id: int
    carrier: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    lines: list[ShipmentLineCreate]


class ShipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    so_id: int
    status: str
    carrier: str | None
    tracking_number: str | None
    notes: str | None
    created_at: datetime
    shipped_at: datetime | None
    lines: list[ShipmentLineRead]
