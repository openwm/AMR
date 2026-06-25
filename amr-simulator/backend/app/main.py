from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect

from . import state
from .config import CORS_ORIGINS, TICK_INTERVAL
from .layout import fetch_layout
from .models import fleet
from .router import router


async def _broadcast(payload: dict) -> None:
    dead: set[WebSocket] = set()
    message = json.dumps(payload)
    for ws in list(state.ws_clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    state.ws_clients.difference_update(dead)


async def _movement_loop() -> None:
    while True:
        await asyncio.sleep(TICK_INTERVAL)
        any_moved = False
        for amr in fleet.values():
            if amr.status != "traveling":
                continue
            if amr.target_x is None or amr.target_y is None:
                amr.status = "idle"
                continue

            step = amr.speed * TICK_INTERVAL
            dx = amr.target_x - amr.x
            dy = amr.target_y - amr.y
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist <= step:
                amr.x = amr.target_x
                amr.y = amr.target_y
                amr.status = "at_location"
            else:
                ratio = step / dist
                amr.x += dx * ratio
                amr.y += dy * ratio
            any_moved = True

        if any_moved:
            await _broadcast({
                "type": "fleet_update",
                "amrs": [a.to_dict() for a in fleet.values()],
            })


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.layout = await fetch_layout()
    task = asyncio.create_task(_movement_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="AMR Simulator", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    state.ws_clients.add(ws)
    # Send full fleet state immediately on connect
    try:
        await ws.send_text(json.dumps({
            "type": "fleet_update",
            "amrs": [a.to_dict() for a in fleet.values()],
        }))
        while True:
            await ws.receive_text()  # keep connection alive; ignore any client messages
    except WebSocketDisconnect:
        pass
    finally:
        state.ws_clients.discard(ws)
