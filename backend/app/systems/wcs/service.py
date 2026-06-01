from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings
from .redis_client import get_redis
from .schemas import CreateTaskRequest, OutboundCarton, PickTask, StationQueue, StationSummary

STATIONS = ["STA-01", "STA-02", "STA-03"]
MAX_QUEUE_DEPTH = 5
MAX_AMR_COUNT = 3
REFILL_THRESHOLD = 3


# ── Redis key helpers ────────────────────────────────────────────────────────

def _task_key(task_id: str) -> str:
    return f"wcs:task:{task_id}"

def _queue_key(sid: str) -> str:
    return f"wcs:station:{sid}:queue"

def _at_dock_key(sid: str) -> str:
    return f"wcs:station:{sid}:at_dock"

def _amr_key(sid: str) -> str:
    return f"wcs:station:{sid}:amr_count"

def _picks_key(sid: str) -> str:
    return f"wcs:station:{sid}:picks"

def _carton_key(carton_id: str) -> str:
    return f"wcs:carton:{carton_id}"

def _so_carton_key(so_id: int) -> str:
    return f"wcs:so:{so_id}:carton"

def _station_carton_key(sid: str) -> str:
    return f"wcs:station:{sid}:active_carton"


# ── Exceptions ───────────────────────────────────────────────────────────────

class WCSError(Exception):
    pass

class NoCapacityError(WCSError):
    pass


# ── Station bootstrap ────────────────────────────────────────────────────────

async def seed_stations() -> None:
    r = get_redis()
    for sid in STATIONS:
        await r.sadd("wcs:stations", sid)
        await r.setnx(_amr_key(sid), 0)


# ── Internal helpers ─────────────────────────────────────────────────────────

async def _get_task(task_id: str) -> PickTask:
    r = get_redis()
    data = await r.hgetall(_task_key(task_id))
    if not data:
        raise WCSError(f"Task {task_id} not found")
    return PickTask(
        id=data["id"],
        order_id=int(data["order_id"]),
        order_line_id=int(data["order_line_id"]),
        product_id=int(data["product_id"]),
        product_sku=data["product_sku"],
        quantity=int(data["quantity"]),
        deadline=datetime.fromisoformat(data["deadline"]),
        priority_score=float(data["priority_score"]),
        station_id=data["station_id"],
        status=data["status"],  # type: ignore[arg-type]
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


async def _save_task(task: PickTask) -> None:
    r = get_redis()
    await r.hset(_task_key(task.id), mapping={
        "id": task.id,
        "order_id": str(task.order_id),
        "order_line_id": str(task.order_line_id),
        "product_id": str(task.product_id),
        "product_sku": task.product_sku,
        "quantity": str(task.quantity),
        "deadline": task.deadline.isoformat(),
        "priority_score": str(task.priority_score),
        "station_id": task.station_id,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    })


async def _rolling_picks_per_hour(sid: str) -> float:
    r = get_redis()
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
    count = await r.zcount(_picks_key(sid), since, "+inf")
    return float(count)


async def _station_stats(sid: str) -> StationSummary:
    r = get_redis()
    queue_depth = (await r.zcard(_queue_key(sid))) + (await r.zcard(_at_dock_key(sid)))
    amr_count = int(await r.get(_amr_key(sid)) or 0)
    picks_hr = await _rolling_picks_per_hour(sid)
    return StationSummary(
        station_id=sid,
        queue_depth=queue_depth,
        amr_count=amr_count,
        picks_per_hour=picks_hr,
    )


async def _promote_to_at_dock(sid: str) -> None:
    """Pop highest-priority task from queue ZSET into at_dock ZSET."""
    r = get_redis()
    result = await r.zpopmin(_queue_key(sid), 1)
    if not result:
        return
    task_id, score = result[0]
    now = datetime.now(timezone.utc)
    await r.zadd(_at_dock_key(sid), {task_id: score})
    task = await _get_task(task_id)
    task.status = "at_dock"
    task.updated_at = now
    await _save_task(task)


# ── Public service functions ─────────────────────────────────────────────────

async def list_stations() -> list[StationSummary]:
    r = get_redis()
    station_ids = sorted(await r.smembers("wcs:stations"))
    return [await _station_stats(sid) for sid in station_ids]


async def create_task(req: CreateTaskRequest) -> PickTask:
    stations = await list_stations()
    eligible = [
        s for s in stations
        if s.queue_depth < MAX_QUEUE_DEPTH and s.amr_count < MAX_AMR_COUNT
    ]
    if not eligible:
        raise NoCapacityError("All stations are at capacity")

    best = min(eligible, key=lambda s: (s.queue_depth, s.amr_count))
    sid = best.station_id

    # Priority score: lower deadline timestamp → higher priority (sorted ascending)
    score = req.deadline.timestamp()
    now = datetime.now(timezone.utc)

    task = PickTask(
        id=str(uuid.uuid4()),
        order_id=req.order_id,
        order_line_id=req.order_line_id,
        product_id=req.product_id,
        product_sku=req.product_sku,
        quantity=req.quantity,
        deadline=req.deadline,
        priority_score=score,
        station_id=sid,
        status="queued",
        created_at=now,
        updated_at=now,
    )

    r = get_redis()
    await _save_task(task)
    await r.zadd(_queue_key(sid), {task.id: score})
    await r.incr(_amr_key(sid))

    # Auto-promote top task to at_dock if dock is empty
    if await r.zcard(_at_dock_key(sid)) == 0:
        await _promote_to_at_dock(sid)

    return await _get_task(task.id)


async def get_station_queue(station_id: str) -> StationQueue:
    r = get_redis()

    at_dock_items = await r.zrange(_at_dock_key(station_id), 0, -1, withscores=False)
    queued_items = await r.zrange(_queue_key(station_id), 0, -1, withscores=False)

    tasks: list[PickTask] = []
    for tid in [*at_dock_items, *queued_items]:
        try:
            tasks.append(await _get_task(tid))
        except WCSError:
            pass

    stats = await _station_stats(station_id)
    return StationQueue(
        station_id=station_id,
        tasks=tasks,
        queue_depth=stats.queue_depth,
        amr_count=stats.amr_count,
        picks_per_hour=stats.picks_per_hour,
    )


async def advance_task(station_id: str, task_id: str) -> PickTask:
    """Move task at_dock → picking."""
    r = get_redis()
    task = await _get_task(task_id)

    if task.station_id != station_id:
        raise WCSError(f"Task {task_id} belongs to station {task.station_id}")
    if task.status != "at_dock":
        raise WCSError(f"Task {task_id} is '{task.status}', expected 'at_dock'")

    await r.zrem(_at_dock_key(station_id), task_id)
    task.status = "picking"
    task.updated_at = datetime.now(timezone.utc)
    await _save_task(task)

    # Promote next queued task to fill the vacated dock slot
    await _promote_to_at_dock(station_id)

    return task


async def complete_task(station_id: str, task_id: str) -> PickTask:
    """Complete a picking task: record pace, patch WMS, trigger refill."""
    r = get_redis()
    task = await _get_task(task_id)

    if task.station_id != station_id:
        raise WCSError(f"Task {task_id} belongs to station {task.station_id}")
    if task.status != "picking":
        raise WCSError(f"Task {task_id} is '{task.status}', expected 'picking'")

    now = datetime.now(timezone.utc)
    task.status = "completed"
    task.updated_at = now
    await _save_task(task)

    # Pace tracker: record pick timestamp, trim entries older than 2 h
    await r.zadd(_picks_key(station_id), {f"{task_id}:{now.timestamp()}": now.timestamp()})
    cutoff = (now - timedelta(hours=2)).timestamp()
    await r.zremrangebyscore(_picks_key(station_id), "-inf", cutoff)

    # Release the AMR slot
    cur = int(await r.get(_amr_key(station_id)) or 0)
    await r.set(_amr_key(station_id), max(0, cur - 1))

    # Notify WMS (best-effort)
    await _patch_wms_order_line(task)

    # Refill check
    queue_depth = await r.zcard(_queue_key(station_id))
    if queue_depth < REFILL_THRESHOLD:
        _log_refill(station_id, int(queue_depth))

    return task


async def exception_task(station_id: str, task_id: str) -> PickTask:
    """Sideline a task; advance the next at_dock task to picking."""
    r = get_redis()
    task = await _get_task(task_id)

    if task.station_id != station_id:
        raise WCSError(f"Task {task_id} belongs to station {task.station_id}")
    if task.status in ("completed", "exception"):
        raise WCSError(f"Task {task_id} is already in terminal state '{task.status}'")

    # Remove from whichever queue it's in
    await r.zrem(_at_dock_key(station_id), task_id)
    await r.zrem(_queue_key(station_id), task_id)

    task.status = "exception"
    task.updated_at = datetime.now(timezone.utc)
    await _save_task(task)

    # Release AMR slot
    cur = int(await r.get(_amr_key(station_id)) or 0)
    await r.set(_amr_key(station_id), max(0, cur - 1))

    # Advance next at_dock task into the active (picking) slot
    at_dock_items = await r.zrange(_at_dock_key(station_id), 0, 0, withscores=False)
    if at_dock_items:
        next_id = at_dock_items[0]
        await r.zrem(_at_dock_key(station_id), next_id)
        next_task = await _get_task(next_id)
        next_task.status = "picking"
        next_task.updated_at = datetime.now(timezone.utc)
        await _save_task(next_task)
    else:
        # No at_dock tasks — promote from queue instead
        await _promote_to_at_dock(station_id)

    return task


# ── Carton management ────────────────────────────────────────────────────────

async def create_carton(so_id: int, so_lines_data: list[dict]) -> OutboundCarton:
    """Create an outbound carton for an SO: pick a home station and create one PickTask per line."""
    stations = await list_stations()
    eligible = [
        s for s in stations
        if s.queue_depth < MAX_QUEUE_DEPTH and s.amr_count < MAX_AMR_COUNT
    ]
    if not eligible:
        raise NoCapacityError("All stations at capacity — cannot create carton")

    home_station = min(eligible, key=lambda s: (s.queue_depth, s.amr_count))

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=24)
    carton_id = str(uuid.uuid4())
    task_ids: list[str] = []

    for line in so_lines_data:
        req = CreateTaskRequest(
            order_id=so_id,
            order_line_id=line["id"],
            product_id=line["product_id"],
            product_sku=line["product_sku"],
            quantity=line["qty_ordered"],
            deadline=deadline,
        )
        task = await create_task(req)
        task_ids.append(task.id)

    r = get_redis()
    await r.hset(_carton_key(carton_id), mapping={
        "id": carton_id,
        "so_id": str(so_id),
        "station_id": home_station.station_id,
        "status": "open",
        "task_ids": ",".join(task_ids),
        "created_at": now.isoformat(),
    })
    await r.set(_so_carton_key(so_id), carton_id)
    await r.set(_station_carton_key(home_station.station_id), carton_id)

    return OutboundCarton(
        id=carton_id,
        so_id=so_id,
        station_id=home_station.station_id,
        status="open",
        task_ids=task_ids,
        created_at=now,
    )


async def get_carton(carton_id: str) -> OutboundCarton:
    r = get_redis()
    data = await r.hgetall(_carton_key(carton_id))
    if not data:
        raise WCSError(f"Carton {carton_id} not found")
    return OutboundCarton(
        id=data["id"],
        so_id=int(data["so_id"]),
        station_id=data["station_id"],
        status=data["status"],  # type: ignore[arg-type]
        task_ids=[t for t in data["task_ids"].split(",") if t],
        created_at=datetime.fromisoformat(data["created_at"]),
    )


async def get_station_active_carton(station_id: str) -> OutboundCarton | None:
    r = get_redis()
    carton_id = await r.get(_station_carton_key(station_id))
    if not carton_id:
        return None
    try:
        return await get_carton(carton_id)
    except WCSError:
        return None


# ── Side-effects ─────────────────────────────────────────────────────────────

async def _patch_wms_order_line(task: PickTask) -> None:
    url = (
        f"{settings.WMS_API_URL}/api/wms/outbound"
        f"/sales-orders/{task.order_id}/lines/{task.order_line_id}"
    )
    async with httpx.AsyncClient() as client:
        try:
            await client.patch(
                url,
                json={"picked_qty": task.quantity},
                timeout=3.0,
            )
        except Exception as exc:
            print(f"[WCS] WMS patch skipped ({exc})")


def _log_refill(station_id: str, depth: int) -> None:
    print(f"[WCS] Refill triggered — {station_id} queue depth {depth} < {REFILL_THRESHOLD}")
