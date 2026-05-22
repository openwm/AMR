from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.reporting import service

router = APIRouter()


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)) -> dict:
    return service.kpis(db)


@router.get("/stock-by-zone")
def get_stock_by_zone(db: Session = Depends(get_db)) -> list[dict]:
    return service.stock_by_zone(db)


@router.get("/throughput")
def get_throughput(
    db: Session = Depends(get_db), days: int = Query(14, ge=1, le=90)
) -> list[dict]:
    return service.throughput(db, days=days)


@router.get("/top-movers")
def get_top_movers(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    return service.top_movers(db, days=days, limit=limit)


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)) -> list[dict]:
    return service.low_stock_products(db)


@router.get("/recent-activity")
def get_recent_activity(
    db: Session = Depends(get_db), limit: int = Query(10, ge=1, le=50)
) -> list[dict]:
    return service.recent_activity(db, limit=limit)
