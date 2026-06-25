from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from .config import AMR_SPEED_DEFAULT

AMRStatus = Literal["idle", "traveling", "at_location"]


@dataclass
class AMR:
    id: str
    name: str
    x: float
    y: float
    target_x: float | None = None
    target_y: float | None = None
    target_location: str | None = None
    status: AMRStatus = "idle"
    speed: float = field(default_factory=lambda: AMR_SPEED_DEFAULT)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "target_x": self.target_x,
            "target_y": self.target_y,
            "target_location": self.target_location,
            "status": self.status,
            "speed": self.speed,
        }


fleet: dict[str, AMR] = {}


def create_amr(name: str, x: float = 0.0, y: float = 0.0, speed: float | None = None) -> AMR:
    amr = AMR(
        id=str(uuid.uuid4()),
        name=name,
        x=x,
        y=y,
        speed=speed if speed is not None else AMR_SPEED_DEFAULT,
    )
    fleet[amr.id] = amr
    return amr


def get_amr(amr_id: str) -> AMR | None:
    return fleet.get(amr_id)
