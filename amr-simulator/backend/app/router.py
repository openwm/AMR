from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import state
from .models import AMR, create_amr, fleet, get_amr

router = APIRouter()


class RegisterAMRRequest(BaseModel):
    name: str
    x: float = 0.0
    y: float = 0.0
    speed: float | None = None


class DispatchRequest(BaseModel):
    location_code: str


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/layout")
def get_layout() -> dict:
    if state.layout is None:
        raise HTTPException(503, "Layout not yet loaded")
    lyt = state.layout
    return {
        "grid_width": lyt.grid_width,
        "grid_height": lyt.grid_height,
        "zone_labels": lyt.zone_labels,
        "locations": {
            code: {"x": c.x, "y": c.y}
            for code, c in lyt.location_coords.items()
        },
        "stations": {
            sid: {"x": c.x, "y": c.y}
            for sid, c in lyt.station_coords.items()
        },
        "dock_in":  {"x": lyt.dock_in_coord.x,  "y": lyt.dock_in_coord.y},
        "dock_out": {"x": lyt.dock_out_coord.x, "y": lyt.dock_out_coord.y},
    }


@router.get("/amrs")
def list_amrs() -> list[dict]:
    return [a.to_dict() for a in fleet.values()]


@router.post("/amrs", status_code=201)
def register_amr(req: RegisterAMRRequest) -> dict:
    amr = create_amr(name=req.name, x=req.x, y=req.y, speed=req.speed)
    return amr.to_dict()


@router.post("/amrs/{amr_id}/dispatch")
def dispatch_amr(amr_id: str, req: DispatchRequest) -> dict:
    amr = get_amr(amr_id)
    if amr is None:
        raise HTTPException(404, f"AMR {amr_id!r} not found")
    return _do_dispatch(amr, req.location_code)


@router.post("/dispatch")
def auto_dispatch(req: DispatchRequest) -> dict:
    """Pick the nearest available (idle or at_location) AMR and dispatch it."""
    available = [a for a in fleet.values() if a.status in ("idle", "at_location")]
    if not available:
        raise HTTPException(503, "No available AMRs (all are traveling)")

    if state.layout is None:
        raise HTTPException(503, "Layout not ready")

    coord = state.layout.location_coords.get(req.location_code)
    if coord is None:
        raise HTTPException(404, f"Location {req.location_code!r} not found in layout")

    def dist(a: AMR) -> float:
        return ((a.x - coord.x) ** 2 + (a.y - coord.y) ** 2) ** 0.5

    nearest = min(available, key=dist)
    return _do_dispatch(nearest, req.location_code)


def _do_dispatch(amr: AMR, location_code: str) -> dict:
    if state.layout is None:
        raise HTTPException(503, "Layout not ready")
    coord = state.layout.location_coords.get(location_code)
    if coord is None:
        raise HTTPException(404, f"Location {location_code!r} not found in layout")
    amr.target_x = coord.x
    amr.target_y = coord.y
    amr.target_location = location_code
    amr.status = "traveling"
    return amr.to_dict()
