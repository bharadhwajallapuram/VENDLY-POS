"""Add user role column

Revision ID: 20250812_02
Revises: 20250812_01
Create Date: 2025-08-12
"""

import sqlalchemy as sa

from alembic import op

revision = "20250812_02"
down_revision = "20250812_01"
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to users table
    # SQLite doesn't support ENUM, so we use String with check constraint
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="clerk")
    )


def downgrade():
    op.drop_column("users", "role")
