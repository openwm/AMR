from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import Device
from .service import DeviceError, get_device, list_devices

router = APIRouter()


@router.get("/", response_model=list[Device])
def get_devices() -> list[Device]:
    return list_devices()


@router.get("/{device_id}", response_model=Device)
def get_device_by_id(device_id: int) -> Device:
    try:
        return get_device(device_id)
    except DeviceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
