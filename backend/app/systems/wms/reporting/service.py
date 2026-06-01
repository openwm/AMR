from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.systems.wms.inbound.models import PurchaseOrder, Receipt
from app.systems.wms.inventory.models import Location, Product, StockItem, StockMovement
from app.systems.wms.outbound.models import SalesOrder, Shipment


def kpis(db: Session) -> dict:
    product_count = db.scalar(select(func.count()).select_from(Product)) or 0
    location_count = db.scalar(select(func.count()).select_from(Location)) or 0

    stock_value = db.scalar(
        select(func.coalesce(func.sum(StockItem.quantity * Product.unit_cost), 0)).select_from(
            StockItem
        ).join(Product, Product.id == StockItem.product_id)
    ) or Decimal("0")

    units_on_hand = db.scalar(
        select(func.coalesce(func.sum(StockItem.quantity), 0))
    ) or 0

    open_pos = db.scalar(
        select(func.count()).select_from(PurchaseOrder).where(
            PurchaseOrder.status.in_(("OPEN", "PARTIAL"))
        )
    ) or 0
    open_sos = db.scalar(
        select(func.count()).select_from(SalesOrder).where(
            SalesOrder.status.in_(("NEW", "ACTIVE", "PARTIAL"))
        )
    ) or 0

    low_stock = db.scalar(
        select(func.count()).select_from(Product).where(
            Product.min_stock > 0,
            Product.min_stock
            > select(func.coalesce(func.sum(StockItem.quantity), 0))
            .where(StockItem.product_id == Product.id)
            .scalar_subquery(),
        )
    ) or 0

    return {
        "product_count": product_count,
        "location_count": location_count,
        "stock_value": float(stock_value),
        "units_on_hand": int(units_on_hand),
        "open_purchase_orders": open_pos,
        "open_sales_orders": open_sos,
        "low_stock_products": low_stock,
    }


def stock_by_zone(db: Session) -> list[dict]:
    rows = db.execute(
        select(Location.zone, func.coalesce(func.sum(StockItem.quantity), 0))
        .join(StockItem, StockItem.location_id == Location.id, isouter=True)
        .group_by(Location.zone)
        .order_by(Location.zone)
    ).all()
    return [{"zone": z, "units": int(qty)} for z, qty in rows]


def throughput(db: Session, days: int = 14) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(
            func.date_trunc("day", StockMovement.created_at).label("day"),
            StockMovement.movement_type,
            func.coalesce(func.sum(func.abs(StockMovement.quantity)), 0),
        )
        .where(StockMovement.created_at >= since)
        .group_by("day", StockMovement.movement_type)
        .order_by("day")
    ).all()

    by_day: dict[str, dict] = {}
    for day, mtype, qty in rows:
        key = day.date().isoformat()
        entry = by_day.setdefault(key, {"day": key, "inbound": 0, "outbound": 0})
        if mtype in ("RECEIPT", "PUTAWAY"):
            entry["inbound"] += int(qty)
        elif mtype in ("PICK", "SHIP"):
            entry["outbound"] += int(qty)
    return sorted(by_day.values(), key=lambda r: r["day"])


def top_movers(db: Session, days: int = 30, limit: int = 10) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(
            Product.sku,
            Product.name,
            func.coalesce(func.sum(func.abs(StockMovement.quantity)), 0),
        )
        .join(StockMovement, StockMovement.product_id == Product.id)
        .where(StockMovement.created_at >= since)
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(func.abs(StockMovement.quantity)).desc())
        .limit(limit)
    ).all()
    return [{"sku": s, "name": n, "units_moved": int(q)} for s, n, q in rows]


def low_stock_products(db: Session) -> list[dict]:
    on_hand = (
        select(StockItem.product_id, func.coalesce(func.sum(StockItem.quantity), 0).label("oh"))
        .group_by(StockItem.product_id)
        .subquery()
    )
    rows = db.execute(
        select(Product.sku, Product.name, Product.min_stock, func.coalesce(on_hand.c.oh, 0))
        .outerjoin(on_hand, on_hand.c.product_id == Product.id)
        .where(Product.min_stock > 0)
        .where(func.coalesce(on_hand.c.oh, 0) < Product.min_stock)
        .order_by((func.coalesce(on_hand.c.oh, 0) - Product.min_stock))
    ).all()
    return [
        {"sku": sku, "name": name, "min_stock": int(ms), "on_hand": int(oh)}
        for sku, name, ms, oh in rows
    ]


def recent_activity(db: Session, limit: int = 10) -> list[dict]:
    receipts = db.execute(
        select(Receipt).order_by(Receipt.created_at.desc()).limit(limit)
    ).scalars().all()
    shipments = db.execute(
        select(Shipment).order_by(Shipment.created_at.desc()).limit(limit)
    ).scalars().all()

    events: list[dict] = []
    for r in receipts:
        events.append({
            "kind": "receipt",
            "reference": r.reference,
            "status": r.status,
            "at": (r.completed_at or r.created_at).isoformat(),
        })
    for s in shipments:
        events.append({
            "kind": "shipment",
            "reference": s.reference,
            "status": s.status,
            "at": (s.shipped_at or s.created_at).isoformat(),
        })
    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]
