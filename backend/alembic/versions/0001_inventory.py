"""inventory module

Revision ID: 0001_inventory
Revises:
Create Date: 2026-05-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_inventory"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uom", sa.String(16), nullable=False, server_default="EA"),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("min_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_barcode", "products", ["barcode"])
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("zone", sa.String(32), nullable=False),
        sa.Column("aisle", sa.String(16), nullable=True),
        sa.Column("rack", sa.String(16), nullable=True),
        sa.Column("bin", sa.String(16), nullable=True),
        sa.Column("type", sa.String(16), nullable=False, server_default="STORAGE"),
        sa.Column("is_pickable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "type IN ('STORAGE', 'RECEIVING', 'SHIPPING', 'QUARANTINE')",
            name="ck_locations_type",
        ),
    )
    op.create_index("ix_locations_code", "locations", ["code"])
    op.create_index("ix_locations_zone", "locations", ["zone"])

    op.create_table(
        "stock_items",
        sa.Column("id", sa.Integer(), primary_key=True),
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
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lot_number", sa.String(64), nullable=False, server_default=""),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "product_id", "location_id", "lot_number", name="uq_stock_items_product_loc_lot"
        ),
    )
    op.create_index("ix_stock_items_product", "stock_items", ["product_id"])
    op.create_index("ix_stock_items_location", "stock_items", ["location_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
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
        sa.Column("movement_type", sa.String(16), nullable=False),
        sa.Column("reference_type", sa.String(32), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("lot_number", sa.String(64), nullable=False, server_default=""),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "movement_type IN ('RECEIPT', 'PUTAWAY', 'PICK', 'SHIP', 'ADJUSTMENT', 'TRANSFER')",
            name="ck_movements_type",
        ),
    )
    op.create_index(
        "ix_movements_product_created", "stock_movements", ["product_id", "created_at"]
    )
    op.create_index("ix_movements_created", "stock_movements", ["created_at"])


def downgrade() -> None:
    op.drop_table("stock_movements")
    op.drop_table("stock_items")
    op.drop_table("locations")
    op.drop_table("products")
