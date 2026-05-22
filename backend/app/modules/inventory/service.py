from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import (
    MOVEMENT_TYPES,
    Location,
    Product,
    StockItem,
    StockMovement,
)


class InventoryError(Exception):
    """Domain error raised by inventory operations."""


def apply_movement(
    db: Session,
    *,
    product_id: int,
    location_id: int,
    quantity: int,
    movement_type: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    lot_number: str = "",
    note: str | None = None,
) -> StockMovement:
    """Create a StockMovement and update the corresponding StockItem atomically.

    Quantity sign convention:
      RECEIPT, PUTAWAY, ADJUSTMENT(+): positive
      PICK, SHIP, ADJUSTMENT(-): negative
    """
    if movement_type not in MOVEMENT_TYPES:
        raise InventoryError(f"Invalid movement_type '{movement_type}'")
    if quantity == 0:
        raise InventoryError("Movement quantity cannot be zero")

    product = db.get(Product, product_id)
    if not product:
        raise InventoryError(f"Product {product_id} not found")
    location = db.get(Location, location_id)
    if not location:
        raise InventoryError(f"Location {location_id} not found")

    stock = db.execute(
        select(StockItem).where(
            StockItem.product_id == product_id,
            StockItem.location_id == location_id,
            StockItem.lot_number == lot_number,
        )
    ).scalar_one_or_none()

    if stock is None:
        if quantity < 0:
            raise InventoryError(
                f"No stock of product {product.sku} at location {location.code} "
                f"(lot='{lot_number}') to decrement"
            )
        stock = StockItem(
            product_id=product_id,
            location_id=location_id,
            quantity=0,
            lot_number=lot_number,
        )
        db.add(stock)

    new_qty = stock.quantity + quantity
    if new_qty < 0:
        raise InventoryError(
            f"Insufficient stock: have {stock.quantity}, requested {-quantity} "
            f"of product {product.sku} at {location.code}"
        )
    stock.quantity = new_qty

    movement = StockMovement(
        product_id=product_id,
        location_id=location_id,
        quantity=quantity,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=reference_id,
        lot_number=lot_number,
        note=note,
    )
    db.add(movement)
    db.flush()
    return movement


def stock_on_hand(db: Session, *, product_id: int) -> int:
    total = db.execute(
        select(StockItem.quantity).where(StockItem.product_id == product_id)
    ).all()
    return sum(row[0] for row in total)
