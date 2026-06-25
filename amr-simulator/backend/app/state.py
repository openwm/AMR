from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .layout import WarehouseLayout
    from fastapi.websockets import WebSocket

# Module-level singletons — safe in single-process uvicorn.
# Both main.py and router.py import this module to avoid circular deps.
layout: "WarehouseLayout | None" = None
ws_clients: set["WebSocket"] = set()
