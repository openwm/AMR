from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import OPENWM_URL

FALLBACK_ZONES = ["A", "B", "C"]
FALLBACK_AISLES = ["01", "02", "03"]
FALLBACK_RACKS = ["01", "02", "03"]
STATION_IDS = ["STA-01", "STA-02", "STA-03"]
LANE_WIDTH = 1  # empty columns between zones for AMR travel lanes


@dataclass
class CellCoord:
    x: float
    y: float


@dataclass
class WarehouseLayout:
    location_coords: dict[str, CellCoord]
    grid_width: int
    grid_height: int
    zone_labels: list[dict]
    dock_in_coord: CellCoord
    dock_out_coord: CellCoord
    station_coords: dict[str, CellCoord]


async def fetch_layout() -> WarehouseLayout:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OPENWM_URL}/api/wms/inventory/locations")
            resp.raise_for_status()
            locations = resp.json()
        print(f"[layout] Loaded {len(locations)} locations from OpenWM")
    except Exception as exc:
        print(f"[layout] Could not reach OpenWM ({exc}), using fallback layout")
        locations = _fallback_locations()

    return _build_layout(locations)


def _fallback_locations() -> list[dict]:
    locs: list[dict] = []
    for zone in FALLBACK_ZONES:
        for aisle in FALLBACK_AISLES:
            for rack in FALLBACK_RACKS:
                locs.append({
                    "code": f"{zone}-{aisle}-{rack}",
                    "zone": zone,
                    "aisle": aisle,
                    "rack": rack,
                    "type": "STORAGE",
                })
    locs.append({"code": "DOCK-IN",  "zone": "DOCK", "aisle": None, "rack": None, "type": "RECEIVING"})
    locs.append({"code": "DOCK-OUT", "zone": "DOCK", "aisle": None, "rack": None, "type": "SHIPPING"})
    return locs


def _build_layout(locations: list[dict]) -> WarehouseLayout:
    storage = [
        loc for loc in locations
        if loc.get("type") == "STORAGE" and loc.get("aisle") and loc.get("rack")
    ]
    dock_in_loc  = next((l for l in locations if l.get("type") == "RECEIVING"), None)
    dock_out_loc = next((l for l in locations if l.get("type") == "SHIPPING"),  None)

    zones = sorted(set(loc["zone"] for loc in storage))

    zone_aisles: dict[str, set[str]] = {}
    zone_racks:  dict[str, set[str]] = {}
    for loc in storage:
        z = loc["zone"]
        zone_aisles.setdefault(z, set()).add(loc["aisle"])
        zone_racks.setdefault(z, set()).add(loc["rack"])

    zone_aisles_sorted = {z: sorted(v) for z, v in zone_aisles.items()}
    zone_racks_sorted  = {z: sorted(v) for z, v in zone_racks.items()}

    # x: each zone gets n_racks columns + LANE_WIDTH gap
    zone_x_start: dict[str, int] = {}
    cursor = 1
    for z in zones:
        zone_x_start[z] = cursor
        cursor += len(zone_racks_sorted[z]) + LANE_WIDTH

    # y: shared aisle numbering across all zones (aisles run floor-wide)
    all_aisles = sorted(set(a for v in zone_aisles_sorted.values() for a in v))
    aisle_y: dict[str, int] = {a: i + 1 for i, a in enumerate(all_aisles)}

    location_coords: dict[str, CellCoord] = {}
    for loc in storage:
        z  = loc["zone"]
        a  = loc["aisle"]
        r  = loc["rack"]
        x  = zone_x_start[z] + zone_racks_sorted[z].index(r)
        y  = aisle_y[a]
        location_coords[loc["code"]] = CellCoord(x=float(x), y=float(y))

    max_y = max(aisle_y.values()) if aisle_y else 1
    grid_width  = cursor - 1
    grid_height = max_y + 2  # row 0 = dock, rows 1..max_y = aisles, row max_y+1 = stations

    # Dock: centered at top
    half = grid_width // 2
    dock_in_coord  = CellCoord(x=float(max(0, half - 1)), y=0.0)
    dock_out_coord = CellCoord(x=float(half + 1),         y=0.0)

    if dock_in_loc:
        location_coords[dock_in_loc["code"]]  = dock_in_coord
    if dock_out_loc:
        location_coords[dock_out_loc["code"]] = dock_out_coord

    # Stations: evenly spaced at bottom row
    station_coords: dict[str, CellCoord] = {}
    step = max(1, grid_width // max(1, len(STATION_IDS)))
    for i, sid in enumerate(STATION_IDS):
        coord = CellCoord(x=float(1 + i * step), y=float(max_y + 1))
        station_coords[sid] = coord
        location_coords[sid] = coord

    zone_labels = [
        {
            "zone": z,
            "x_start": zone_x_start[z],
            "x_end": zone_x_start[z] + len(zone_racks_sorted[z]) - 1,
        }
        for z in zones
    ]

    return WarehouseLayout(
        location_coords=location_coords,
        grid_width=grid_width,
        grid_height=grid_height,
        zone_labels=zone_labels,
        dock_in_coord=dock_in_coord,
        dock_out_coord=dock_out_coord,
        station_coords=station_coords,
    )
