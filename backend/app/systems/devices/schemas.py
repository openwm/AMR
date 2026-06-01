from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DeviceType = Literal["HANDHELD_SCANNER", "TABLET", "LABEL_PRINTER", "FIXED_SCANNER", "DISPLAY"]
DeviceStatus = Literal["ONLINE", "OFFLINE", "CHARGING", "ERROR"]


class Device(BaseModel):
    id: int
    device_code: str
    name: str
    type: DeviceType
    status: DeviceStatus
    ip_address: str | None
    battery_pct: int | None
    firmware_version: str | None
    location: str | None
    last_seen: datetime | None


class RegisterDevice(BaseModel):
    device_code: str
    name: str
    type: DeviceType
    ip_address: str | None = None
    firmware_version: str | None = None
    location: str | None = None


class UpdateDeviceStatus(BaseModel):
    status: DeviceStatus
    battery_pct: int | None = None
    ip_address: str | None = None
    location: str | None = None
