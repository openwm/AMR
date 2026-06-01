from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

SO_STATUSES = ("DRAFT", "NEW", "ACTIVE", "PICKING", "PARTIAL", "SHIPPED", "CLOSED", "CANCELLED")
SHIPMENT_STATUSES = ("DRAFT", "SHIPPED")


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    __table_args__ = (
        CheckConstraint(f"status IN {SO_STATUSES}", name="ck_so_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    customer: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="NEW")
    requested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lines: Mapped[list["SOLine"]] = relationship(
        back_populates="so", cascade="all, delete-orphan", lazy="selectin"
    )


class SOLine(Base):
    __tablename__ = "so_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    so_id: Mapped[int] = mapped_column(
        ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_shipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qty_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    so: Mapped[SalesOrder] = relationship(back_populates="lines")


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(f"status IN {SHIPMENT_STATUSES}", name="ck_shipment_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    so_id: Mapped[int] = mapped_column(
        ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    carrier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    lines: Mapped[list["ShipmentLine"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan", lazy="selectin"
    )


class ShipmentLine(Base):
    __tablename__ = "shipment_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False
    )
    so_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("so_lines.id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    lot_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    shipment: Mapped[Shipment] = relationship(back_populates="lines")
