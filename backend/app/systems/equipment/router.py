from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import EquipmentAsset, MaintenanceRecord
from .service import EquipmentError, get_asset, list_assets, list_maintenance

router = APIRouter()


@router.get("/assets", response_model=list[EquipmentAsset])
def get_assets() -> list[EquipmentAsset]:
    return list_assets()


@router.get("/assets/{asset_id}", response_model=EquipmentAsset)
def get_asset_by_id(asset_id: int) -> EquipmentAsset:
    try:
        return get_asset(asset_id)
    except EquipmentError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/assets/{asset_id}/maintenance", response_model=list[MaintenanceRecord])
def get_maintenance(asset_id: int) -> list[MaintenanceRecord]:
    return list_maintenance(asset_id)
