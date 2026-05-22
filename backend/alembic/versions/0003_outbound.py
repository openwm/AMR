"""outbound module

Revision ID: 0003_outbound
Revises: 0002_inbound
Create Date: 2026-05-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_outbound"
down_revision: Union[str, None] = "0002_inbound"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(32), nullable=False, unique=True),
        sa.Column("customer", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
        sa.Column("requested_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'PARTIAL', 'SHIPPED', 'CLOSED', 'CANCELLED')",
            name="ck_so_status",
        ),
    )
    op.create_index("ix_sales_orders_reference", "sales_orders", ["reference"])

    op.create_table(
        "so_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "so_id",
            sa.Integer(),
            sa.ForeignKey("sales_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty_ordered", sa.Integer(), nullable=False),
        sa.Column("qty_shipped", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(32), nullable=False, unique=True),
        sa.Column(
            "so_id",
            sa.Integer(),
            sa.ForeignKey("sales_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("carrier", sa.String(64), nullable=True),
        sa.Column("tracking_number", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SHIPPED')", name="ck_shipment_status"
        ),
    )
    op.create_index("ix_shipments_reference", "shipments", ["reference"])

    op.create_table(
        "shipment_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "shipment_id",
            sa.Integer(),
            sa.ForeignKey("shipments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "so_line_id",
            sa.Integer(),
            sa.ForeignKey("so_lines.id", ondelete="SET NULL"),
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
    )


def downgrade() -> None:
    op.drop_table("shipment_lines")
    op.drop_table("shipments")
    op.drop_table("so_lines")
    op.drop_table("sales_orders")
