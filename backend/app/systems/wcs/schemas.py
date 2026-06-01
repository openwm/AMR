from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TaskStatus = Literal["queued", "at_dock", "picking", "completed", "exception"]


class CreateTaskRequest(BaseModel):
    order_id: int
    order_line_id: int
    product_id: int
    product_sku: str
    quantity: int
    deadline: datetime


class PickTask(BaseModel):
    id: str
    order_id: int
    order_line_id: int
    product_id: int
    product_sku: str
    quantity: int
    deadline: datetime
    priority_score: float
    station_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class StationQueue(BaseModel):
    station_id: str
    tasks: list[PickTask]
    queue_depth: int
    amr_count: int
    picks_per_hour: float


class StationSummary(BaseModel):
    station_id: str
    queue_depth: int
    amr_count: int
    picks_per_hour: float


class OutboundCarton(BaseModel):
    id: str
    so_id: int
    station_id: str
    status: Literal["open", "closed"]
    task_ids: list[str]
    created_at: datetime
