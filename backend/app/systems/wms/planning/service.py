from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.systems.wms.inventory.models import Product, StockItem
from app.systems.wms.inventory.service import available_qty
from app.systems.wms.outbound.models import SalesOrder
from app.systems.wms.planning.models import PlanningConfig
from app.systems.wms.planning.schemas import OrderAvailability, PlanningResult, ReleaseResult


class PlanningError(Exception):
    pass


def get_config(db: Session) -> PlanningConfig:
    config = db.execute(select(PlanningConfig)).scalar_one_or_none()
    if config is None:
        config = PlanningConfig(max_active_orders=10, max_picking_orders=10)
        db.add(config)
        db.flush()
    return config


def update_config(
    db: Session,
    *,
    max_active_orders: int | None = None,
    max_picking_orders: int | None = None,
) -> PlanningConfig:
    config = get_config(db)
    if max_active_orders is not None:
        config.max_active_orders = max_active_orders
    if max_picking_orders is not None:
        config.max_picking_orders = max_picking_orders
    db.flush()
    return config


def _can_allocate(db: Session, order: SalesOrder) -> tuple[bool, list[int]]:
    missing: list[int] = []
    for line in order.lines:
        if available_qty(db, product_id=line.product_id) < line.qty_ordered:
            missing.append(line.product_id)
    return (len(missing) == 0, missing)


def _allocate_order(db: Session, order: SalesOrder) -> None:
    """Mark enough AVAILABLE StockItems as ALLOCATED to cover each SO line (FIFO)."""
    for line in order.lines:
        remaining = line.qty_ordered
        stock_items = db.execute(
            select(StockItem)
            .where(
                StockItem.product_id == line.product_id,
                StockItem.status == "AVAILABLE",
                StockItem.quantity > 0,
            )
            .order_by(StockItem.updated_at)
        ).scalars().all()

        for item in stock_items:
            if remaining <= 0:
                break
            item.status = "ALLOCATED"
            remaining -= item.quantity

    order.status = "ACTIVE"


def run_planning(db: Session) -> PlanningResult:
    config = get_config(db)

    active_count: int = db.execute(
        select(func.count()).where(SalesOrder.status == "ACTIVE")
    ).scalar_one()

    slots = config.max_active_orders - active_count
    if slots <= 0:
        return PlanningResult(activated=0, skipped=0, slots_remaining=0)

    new_orders = db.execute(
        select(SalesOrder)
        .where(SalesOrder.status == "NEW")
        .order_by(SalesOrder.created_at)
        .limit(slots)
    ).scalars().all()

    activated = 0
    skipped = 0
    for order in new_orders:
        ok, _ = _can_allocate(db, order)
        if ok:
            _allocate_order(db, order)
            activated += 1
        else:
            skipped += 1

    return PlanningResult(
        activated=activated,
        skipped=skipped,
        slots_remaining=slots - activated,
    )


def list_new_orders_with_availability(db: Session) -> list[OrderAvailability]:
    new_orders = db.execute(
        select(SalesOrder)
        .where(SalesOrder.status == "NEW")
        .order_by(SalesOrder.created_at)
    ).scalars().all()

    result: list[OrderAvailability] = []
    for order in new_orders:
        can_fulfill, missing = _can_allocate(db, order)
        result.append(
            OrderAvailability(
                so_id=order.id,
                reference=order.reference,
                customer=order.customer,
                created_at=order.created_at,
                can_fulfill=can_fulfill,
                missing_product_ids=missing,
            )
        )
    return result


async def release_to_wcs(db: Session) -> ReleaseResult:
    """Release ACTIVE orders to WCS: create a carton + pick tasks per order, set status to PICKING."""
    from app.systems.wcs import service as wcs_service

    config = get_config(db)

    picking_count: int = db.execute(
        select(func.count()).where(SalesOrder.status == "PICKING")
    ).scalar_one()

    slots = config.max_picking_orders - picking_count
    if slots <= 0:
        return ReleaseResult(released=0, skipped=0)

    active_orders = db.execute(
        select(SalesOrder)
        .where(SalesOrder.status == "ACTIVE")
        .order_by(SalesOrder.created_at)
        .limit(slots)
    ).scalars().all()

    released = 0
    skipped = 0
    for so in active_orders:
        # Collect plain-dict data before any await to avoid DetachedInstanceError
        so_id = so.id
        so_lines_data = [
            {
                "id": ln.id,
                "product_id": ln.product_id,
                "product_sku": (db.get(Product, ln.product_id) or type("P", (), {"sku": str(ln.product_id)})()).sku,
                "qty_ordered": ln.qty_ordered,
            }
            for ln in so.lines
        ]

        try:
            await wcs_service.create_carton(so_id=so_id, so_lines_data=so_lines_data)
            so.status = "PICKING"
            released += 1
        except wcs_service.NoCapacityError:
            skipped += 1
            break

    return ReleaseResult(released=released, skipped=skipped)
