"""inbound module

Revision ID: 0002_inbound
Revises: 0001_inventory
Create Date: 2026-05-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_inbound"
down_revision: Union[str, None] = "0001_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(32), nullable=False, unique=True),
        sa.Column("supplier", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'PARTIAL', 'RECEIVED', 'CLOSED')",
            name="ck_po_status",
        ),
    )
    op.create_index("ix_purchase_orders_reference", "purchase_orders", ["reference"])

    op.create_table(
        "po_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "po_id",
            sa.Integer(),
            sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty_ordered", sa.Integer(), nullable=False),
        sa.Column("qty_received", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(32), nullable=False, unique=True),
        sa.Column(
            "po_id",
            sa.Integer(),
            sa.ForeignKey("purchase_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'COMPLETED')", name="ck_receipt_status"),
    )
    op.create_index("ix_receipts_reference", "receipts", ["reference"])

    op.create_table(
        "receipt_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "receipt_id",
            sa.Integer(),
            sa.ForeignKey("receipts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "po_line_id",
            sa.Integer(),
            sa.ForeignKey("po_lines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("lot_number", sa.String(64), nullable=False, server_default=""),
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("receipt_lines")
    op.drop_table("receipts")
    op.drop_table("po_lines")
    op.drop_table("purchase_orders")
