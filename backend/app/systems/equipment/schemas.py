from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EquipmentType = Literal["FORKLIFT", "PALLET_JACK", "CONVEYOR", "DOCK_DOOR", "SORTER", "CRANE"]
EquipmentStatus = Literal["AVAILABLE", "IN_USE", "MAINTENANCE", "OFFLINE"]


class EquipmentAsset(BaseModel):
    id: int
    asset_code: str
    name: str
    type: EquipmentType
    status: EquipmentStatus
    location: str | None
    hours_operated: float
    next_service_at: datetime | None
    notes: str | None


class CreateEquipmentAsset(BaseModel):
    asset_code: str
    name: str
    type: EquipmentType
    location: str | None = None
    notes: str | None = None


class UpdateEquipmentStatus(BaseModel):
    status: EquipmentStatus
    location: str | None = None
    notes: str | None = None


class MaintenanceRecord(BaseModel):
    id: int
    asset_id: int
    performed_at: datetime
    technician: str
    description: str
    hours_at_service: float
