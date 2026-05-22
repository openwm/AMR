from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

LOCATION_TYPES = ("STORAGE", "RECEIVING", "SHIPPING", "QUARANTINE")
MOVEMENT_TYPES = ("RECEIPT", "PUTAWAY", "PICK", "SHIP", "ADJUSTMENT", "TRANSFER")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint(f"type IN {LOCATION_TYPES}", name="ck_locations_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    aisle: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rack: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="STORAGE")
    is_pickable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "location_id", "lot_number", name="uq_stock_items_product_loc_lot"
        ),
        Index("ix_stock_items_product", "product_id"),
        Index("ix_stock_items_location", "location_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lot_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped[Product] = relationship(lazy="joined")
    location: Mapped[Location] = relationship(lazy="joined")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint(f"movement_type IN {MOVEMENT_TYPES}", name="ck_movements_type"),
        Index("ix_movements_product_created", "product_id", "created_at"),
        Index("ix_movements_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(16), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    product: Mapped[Product] = relationship(lazy="joined")
    location: Mapped[Location] = relationship(lazy="joined")
