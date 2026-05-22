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

PO_STATUSES = ("DRAFT", "OPEN", "PARTIAL", "RECEIVED", "CLOSED")
RECEIPT_STATUSES = ("DRAFT", "COMPLETED")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint(f"status IN {PO_STATUSES}", name="ck_po_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    supplier: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lines: Mapped[list["POLine"]] = relationship(
        back_populates="po", cascade="all, delete-orphan", lazy="selectin"
    )


class POLine(Base):
    __tablename__ = "po_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    po: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (
        CheckConstraint(f"status IN {RECEIPT_STATUSES}", name="ck_receipt_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    po_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    lines: Mapped[list["ReceiptLine"]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan", lazy="selectin"
    )


class ReceiptLine(Base):
    __tablename__ = "receipt_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    po_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("po_lines.id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    lot_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    receipt: Mapped[Receipt] = relationship(back_populates="lines")
