"""picking flow — qty_picked on so_lines, PICKING status, max_picking_orders

Revision ID: 0005_picking_flow
Revises: 0004_planning
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_picking_flow"
down_revision: Union[str, None] = "0004_planning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "so_lines",
        sa.Column("qty_picked", sa.Integer(), nullable=False, server_default="0"),
    )

    op.drop_constraint("ck_so_status", "sales_orders")
    op.create_check_constraint(
        "ck_so_status",
        "sales_orders",
        "status IN ('DRAFT', 'NEW', 'ACTIVE', 'PICKING', 'PARTIAL', 'SHIPPED', 'CLOSED', 'CANCELLED')",
    )

    op.add_column(
        "planning_config",
        sa.Column("max_picking_orders", sa.Integer(), nullable=False, server_default="10"),
    )


def downgrade() -> None:
    op.drop_column("planning_config", "max_picking_orders")

    op.drop_constraint("ck_so_status", "sales_orders")
    op.execute("UPDATE sales_orders SET status = 'ACTIVE' WHERE status = 'PICKING'")
    op.create_check_constraint(
        "ck_so_status",
        "sales_orders",
        "status IN ('DRAFT', 'NEW', 'ACTIVE', 'PARTIAL', 'SHIPPED', 'CLOSED', 'CANCELLED')",
    )

    op.drop_column("so_lines", "qty_picked")
