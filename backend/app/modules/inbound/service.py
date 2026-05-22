from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.inbound.models import POLine, PurchaseOrder, Receipt
from app.modules.inventory.service import InventoryError, apply_movement


class InboundError(Exception):
    pass


def complete_receipt(db: Session, receipt: Receipt) -> Receipt:
    """Apply all receipt lines to stock and update the parent PO progress."""
    if receipt.status == "COMPLETED":
        raise InboundError(f"Receipt {receipt.reference} already completed")

    for line in receipt.lines:
        try:
            apply_movement(
                db,
                product_id=line.product_id,
                location_id=line.location_id,
                quantity=line.quantity,
                movement_type="RECEIPT",
                reference_type="receipt",
                reference_id=receipt.id,
                lot_number=line.lot_number,
            )
        except InventoryError as e:
            raise InboundError(str(e)) from e

        if line.po_line_id:
            po_line = db.get(POLine, line.po_line_id)
            if po_line:
                po_line.qty_received += line.quantity

    if receipt.po_id:
        po = db.get(PurchaseOrder, receipt.po_id)
        if po:
            totals = [(ln.qty_ordered, ln.qty_received) for ln in po.lines]
            if all(rcv >= ord_ for ord_, rcv in totals) and totals:
                po.status = "RECEIVED"
            elif any(rcv > 0 for _, rcv in totals):
                po.status = "PARTIAL"

    receipt.status = "COMPLETED"
    receipt.completed_at = datetime.now(timezone.utc)
    return receipt
