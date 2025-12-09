"""Add coupon fields to sales

Revision ID: 20251208_01
Revises: 20250812_02
Create Date: 2025-12-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20251208_01"
down_revision = "20250812_02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales", sa.Column("order_discount", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("coupon_discount", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("coupon_code", sa.String(length=50), nullable=True))

    # Backfill existing rows to ensure defaults apply
    op.execute("UPDATE sales SET order_discount = 0, coupon_discount = 0 WHERE order_discount IS NULL OR coupon_discount IS NULL")


def downgrade():
    op.drop_column("sales", "coupon_code")
    op.drop_column("sales", "coupon_discount")
    op.drop_column("sales", "order_discount")
