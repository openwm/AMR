from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanningConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    max_active_orders: int
    max_picking_orders: int


class PlanningConfigUpdate(BaseModel):
    max_active_orders: int | None = None
    max_picking_orders: int | None = None


class OrderAvailability(BaseModel):
    so_id: int
    reference: str
    customer: str
    created_at: datetime
    can_fulfill: bool
    missing_product_ids: list[int]


class PlanningResult(BaseModel):
    activated: int
    skipped: int
    slots_remaining: int


class ReleaseResult(BaseModel):
    released: int
    skipped: int
