from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.systems.wms.planning import schemas, service

router = APIRouter()


@router.get("/config", response_model=schemas.PlanningConfigRead)
def get_config(db: Session = Depends(get_db)):
    return service.get_config(db)


@router.patch("/config", response_model=schemas.PlanningConfigRead)
def update_config(
    payload: schemas.PlanningConfigUpdate, db: Session = Depends(get_db)
):
    config = service.update_config(
        db,
        max_active_orders=payload.max_active_orders,
        max_picking_orders=payload.max_picking_orders,
    )
    db.commit()
    db.refresh(config)
    return config


@router.post("/run", response_model=schemas.PlanningResult)
def run_planning(db: Session = Depends(get_db)):
    result = service.run_planning(db)
    db.commit()
    return result


@router.post("/release", response_model=schemas.ReleaseResult)
async def release_to_wcs(db: Session = Depends(get_db)):
    result = await service.release_to_wcs(db)
    db.commit()
    return result


@router.get("/new-orders", response_model=list[schemas.OrderAvailability])
def list_new_orders(db: Session = Depends(get_db)):
    return service.list_new_orders_with_availability(db)
