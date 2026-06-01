from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import CreateTaskRequest, OutboundCarton, PickTask, StationQueue, StationSummary
from .service import (
    NoCapacityError,
    WCSError,
    advance_task,
    complete_task,
    create_task,
    exception_task,
    get_carton,
    get_station_active_carton,
    get_station_queue,
    list_stations,
)

router = APIRouter()


@router.get("/stations", response_model=list[StationSummary])
async def get_stations() -> list[StationSummary]:
    return await list_stations()


@router.post("/tasks", response_model=PickTask, status_code=201)
async def post_task(req: CreateTaskRequest) -> PickTask:
    try:
        return await create_task(req)
    except NoCapacityError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/stations/{station_id}/queue", response_model=StationQueue)
async def get_queue(station_id: str) -> StationQueue:
    return await get_station_queue(station_id)


@router.get("/stations/{station_id}/active-carton", response_model=OutboundCarton | None)
async def get_active_carton(station_id: str) -> OutboundCarton | None:
    return await get_station_active_carton(station_id)


@router.get("/cartons/{carton_id}", response_model=OutboundCarton)
async def get_carton_by_id(carton_id: str) -> OutboundCarton:
    try:
        return await get_carton(carton_id)
    except WCSError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/stations/{station_id}/tasks/{task_id}/advance", response_model=PickTask)
async def post_advance(station_id: str, task_id: str) -> PickTask:
    try:
        return await advance_task(station_id, task_id)
    except WCSError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/stations/{station_id}/tasks/{task_id}/complete", response_model=PickTask)
async def post_complete(station_id: str, task_id: str) -> PickTask:
    try:
        return await complete_task(station_id, task_id)
    except WCSError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/stations/{station_id}/tasks/{task_id}/exception", response_model=PickTask)
async def post_exception(station_id: str, task_id: str) -> PickTask:
    try:
        return await exception_task(station_id, task_id)
    except WCSError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
