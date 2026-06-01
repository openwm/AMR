from __future__ import annotations

from .schemas import EquipmentAsset, MaintenanceRecord


class EquipmentError(Exception):
    pass


def list_assets() -> list[EquipmentAsset]:
    return []


def get_asset(asset_id: int) -> EquipmentAsset:
    raise EquipmentError(f"Asset {asset_id} not found")


def list_maintenance(asset_id: int) -> list[MaintenanceRecord]:
    return []
