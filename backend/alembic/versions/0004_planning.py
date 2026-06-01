"""planning module

Revision ID: 0004_planning
Revises: 0003_outbound
Create Date: 2026-05-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_planning"
down_revision: Union[str, None] = "0003_outbound"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to stock_items (AVAILABLE / ALLOCATED)
    op.add_column(
        "stock_items",
        sa.Column("status", sa.String(16), nullable=False, server_default="AVAILABLE"),
    )
    op.create_check_constraint(
        "ck_stock_status",
        "stock_items",
        "status IN ('AVAILABLE', 'ALLOCATED')",
    )

    # Replace the SO status check constraint to include NEW and ACTIVE
    op.drop_constraint("ck_so_status", "sales_orders")
    op.create_check_constraint(
        "ck_so_status",
        "sales_orders",
        "status IN ('DRAFT', 'NEW', 'ACTIVE', 'PARTIAL', 'SHIPPED', 'CLOSED', 'CANCELLED')",
    )
    # Migrate existing OPEN orders to NEW
    op.execute("UPDATE sales_orders SET status = 'NEW' WHERE status = 'OPEN'")

    # Planning configuration table
    op.create_table(
        "planning_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "max_active_orders", sa.Integer(), nullable=False, server_default="10"
        ),
    )
    op.execute("INSERT INTO planning_config (max_active_orders) VALUES (10)")


def downgrade() -> None:
    op.drop_table("planning_config")

    op.drop_constraint("ck_so_status", "sales_orders")
    op.create_check_constraint(
        "ck_so_status",
        "sales_orders",
        "status IN ('DRAFT', 'OPEN', 'PARTIAL', 'SHIPPED', 'CLOSED', 'CANCELLED')",
    )
    op.execute("UPDATE sales_orders SET status = 'OPEN' WHERE status IN ('NEW', 'ACTIVE')")

    op.drop_constraint("ck_stock_status", "stock_items")
    op.drop_column("stock_items", "status")
