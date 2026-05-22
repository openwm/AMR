from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.inventory.service import InventoryError, apply_movement
from app.modules.outbound.models import SalesOrder, Shipment, SOLine


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
