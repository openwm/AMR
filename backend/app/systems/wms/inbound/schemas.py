from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class POLineCreate(BaseModel):
    product_id: int
    qty_ordered: int = Field(..., gt=0)


class POLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty_ordered: int
    qty_received: int


class POCreate(BaseModel):
    reference: str
    supplier: str
    expected_date: date | None = None
    notes: str | None = None
    lines: list[POLineCreate]


class PORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    supplier: str
    status: str
    expected_date: date | None
    notes: str | None
    created_at: datetime
    lines: list[POLineRead]


class POStatusUpdate(BaseModel):
    status: str


class ReceiptLineCreate(BaseModel):
    po_line_id: int | None = None
    product_id: int
    location_id: int
    quantity: int = Field(..., gt=0)
    lot_number: str = ""
    expiry_date: date | None = None


class ReceiptLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    po_line_id: int | None
    product_id: int
    location_id: int
    quantity: int
    lot_number: str
    expiry_date: date | None


class ReceiptCreate(BaseModel):
    reference: str
    po_id: int | None = None
    notes: str | None = None
    lines: list[ReceiptLineCreate]


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    po_id: int | None
    status: str
    notes: str | None
    created_at: datetime
    completed_at: datetime | None
    lines: list[ReceiptLineRead]
