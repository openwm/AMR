from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.systems.wms.inventory.models import StockItem
from app.systems.wms.inventory.service import InventoryError, apply_movement
from app.systems.wms.outbound.models import SalesOrder, Shipment, ShipmentLine, SOLine


class OutboundError(Exception):
    pass


def ship(db: Session, shipment: Shipment) -> Shipment:
    """Apply pick movements for every shipment line and update the parent SO."""
    if shipment.status == "SHIPPED":
        raise OutboundError(f"Shipment {shipment.reference} already shipped")

    for line in shipment.lines:
        try:
            apply_movement(
                db,
                product_id=line.product_id,
                location_id=line.location_id,
                quantity=-line.quantity,
                movement_type="PICK",
                reference_type="shipment",
                reference_id=shipment.id,
                lot_number=line.lot_number,
            )
        except InventoryError as e:
            raise OutboundError(str(e)) from e

        if line.so_line_id:
            so_line = db.get(SOLine, line.so_line_id)
            if so_line:
                so_line.qty_shipped += line.quantity

    so = db.get(SalesOrder, shipment.so_id)
    if so:
        totals = [(ln.qty_ordered, ln.qty_shipped) for ln in so.lines]
        if all(shp >= ord_ for ord_, shp in totals) and totals:
            so.status = "SHIPPED"
        elif any(shp > 0 for _, shp in totals):
            so.status = "PARTIAL"

    shipment.status = "SHIPPED"
    shipment.shipped_at = datetime.now(timezone.utc)
    return shipment


def record_line_picked(db: Session, so_id: int, line_id: int, picked_qty: int) -> SOLine:
    """Update qty_picked on a SO line (called by WCS callback). Auto-ships when all lines are fully picked."""
    so = db.get(SalesOrder, so_id)
    if not so:
        raise OutboundError(f"Sales order {so_id} not found")
    if so.status not in ("PICKING", "ACTIVE"):
        raise OutboundError(f"Sales order {so_id} is '{so.status}', expected PICKING or ACTIVE")

    line = db.get(SOLine, line_id)
    if not line or line.so_id != so_id:
        raise OutboundError(f"Line {line_id} not found on order {so_id}")

    line.qty_picked = min(line.qty_ordered, line.qty_picked + picked_qty)

    if all(ln.qty_picked >= ln.qty_ordered for ln in so.lines):
        _auto_ship(db, so)

    return line


def _auto_ship(db: Session, so: SalesOrder) -> Shipment:
    """Build a shipment from ALLOCATED stock items and ship it."""
    ref = f"AUTO-{so.id:06d}"
    existing = db.execute(select(Shipment).where(Shipment.reference == ref)).scalar_one_or_none()
    if existing:
        return existing

    shipment = Shipment(
        reference=ref,
        so_id=so.id,
        notes="Auto-created by WCS picking completion",
    )

    for line in so.lines:
        remaining = line.qty_ordered - line.qty_shipped
        if remaining <= 0:
            continue

        stock_items = db.execute(
            select(StockItem)
            .where(
                StockItem.product_id == line.product_id,
                StockItem.status == "ALLOCATED",
                StockItem.quantity > 0,
            )
            .order_by(StockItem.updated_at)
        ).scalars().all()

        for item in stock_items:
            if remaining <= 0:
                break
            take = min(remaining, item.quantity)
            shipment.lines.append(
                ShipmentLine(
                    so_line_id=line.id,
                    product_id=line.product_id,
                    location_id=item.location_id,
                    quantity=take,
                    lot_number=item.lot_number,
                )
            )
            remaining -= take

    db.add(shipment)
    db.flush()
    ship(db, shipment)
    return shipment
