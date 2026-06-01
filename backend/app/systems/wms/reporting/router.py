from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.systems.wms.reporting import service
from app.systems.wms.reporting.schemas import (
    ActivityEvent,
    Kpis,
    LowStockProduct,
    StockByZone,
    ThroughputDay,
    TopMover,
)

router = APIRouter()


@router.get("/kpis", response_model=Kpis)
def get_kpis(db: Session = Depends(get_db)) -> Kpis:
    return service.kpis(db)


@router.get("/stock-by-zone", response_model=list[StockByZone])
def get_stock_by_zone(db: Session = Depends(get_db)) -> list[StockByZone]:
    return service.stock_by_zone(db)


@router.get("/throughput", response_model=list[ThroughputDay])
def get_throughput(
    db: Session = Depends(get_db), days: int = Query(14, ge=1, le=90)
) -> list[ThroughputDay]:
    return service.throughput(db, days=days)


@router.get("/top-movers", response_model=list[TopMover])
def get_top_movers(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(10, ge=1, le=50),
) -> list[TopMover]:
    return service.top_movers(db, days=days, limit=limit)


@router.get("/low-stock", response_model=list[LowStockProduct])
def get_low_stock(db: Session = Depends(get_db)) -> list[LowStockProduct]:
    return service.low_stock_products(db)


@router.get("/recent-activity", response_model=list[ActivityEvent])
def get_recent_activity(
    db: Session = Depends(get_db), limit: int = Query(10, ge=1, le=50)
) -> list[ActivityEvent]:
    return service.recent_activity(db, limit=limit)
