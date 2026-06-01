from __future__ import annotations

from .schemas import Device


class DeviceError(Exception):
    pass


def list_devices() -> list[Device]:
    return []


def get_device(device_id: int) -> Device:
    raise DeviceError(f"Device {device_id} not found")
