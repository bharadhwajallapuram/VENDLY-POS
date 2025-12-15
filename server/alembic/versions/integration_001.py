"""Create integration tables

Revision ID: integration_001
Revises:
Create Date: 2024-12-15 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "integration_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create integration_configs table
    op.create_table(
        "integration_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum(
                "quickbooks",
                "xero",
                "freshbooks",
                "wave",
                "sap",
                "oracle_netsuite",
                "microsoft_dynamics",
                "shopify",
                "woocommerce",
                "magento",
                "etsy",
                "amazon",
                "square",
                "clover",
                name="integrationprovider",
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("api_key", sa.String(512), nullable=False),
        sa.Column("api_secret", sa.String(512), nullable=True),
        sa.Column("webhook_url", sa.String(255), nullable=True),
        sa.Column("webhook_secret", sa.String(255), nullable=True),
        sa.Column(
            "sync_direction",
            sa.Enum("inbound", "outbound", "bidirectional", name="syncdirection"),
            default="bidirectional",
        ),
        sa.Column("sync_frequency", sa.Integer(), default=3600),
        sa.Column("sync_sales", sa.Boolean(), default=True),
        sa.Column("sync_inventory", sa.Boolean(), default=True),
        sa.Column("sync_customers", sa.Boolean(), default=False),
        sa.Column("sync_products", sa.Boolean(), default=False),
        sa.Column("sync_payments", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column(
            "last_sync_status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                "partial",
                name="syncstatus",
            ),
            nullable=True,
        ),
        sa.Column("extra_config", sa.JSON(), default={}),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_integration_configs_provider"),
        "integration_configs",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_configs_is_active"),
        "integration_configs",
        ["is_active"],
        unique=False,
    )

    # Create integration_sync_logs table
    op.create_table(
        "integration_sync_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column(
            "sync_type",
            sa.Enum(
                "sales",
                "inventory",
                "customers",
                "products",
                "payments",
                "orders",
                name="synctype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                "partial",
                name="syncstatus",
            ),
            default="pending",
        ),
        sa.Column("records_processed", sa.Integer(), default=0),
        sa.Column("records_created", sa.Integer(), default=0),
        sa.Column("records_updated", sa.Integer(), default=0),
        sa.Column("records_failed", sa.Integer(), default=0),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", sa.JSON(), default=None),
        sa.Column("response_data", sa.JSON(), default={}),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["integration_configs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_integration_sync_logs_config_id"),
        "integration_sync_logs",
        ["config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_sync_logs_sync_type"),
        "integration_sync_logs",
        ["sync_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_sync_logs_status"),
        "integration_sync_logs",
        ["status"],
        unique=False,
    )

    # Create integration_mappings table
    op.create_table(
        "integration_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("vendly_field", sa.String(255), nullable=False),
        sa.Column("external_field", sa.String(255), nullable=False),
        sa.Column("field_type", sa.String(50), default="string"),
        sa.Column("transformation", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["integration_configs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create integration_webhooks table
    op.create_table(
        "integration_webhooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("webhook_type", sa.String(100), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("signature", sa.String(512), nullable=True),
        sa.Column("processed", sa.Boolean(), default=False),
        sa.Column(
            "processing_status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                "partial",
                name="syncstatus",
            ),
            nullable=True,
        ),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["integration_configs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_integration_webhooks_processed"),
        "integration_webhooks",
        ["processed"],
        unique=False,
    )


def downgrade():
    op.drop_table("integration_webhooks")
    op.drop_table("integration_mappings")
    op.drop_table("integration_sync_logs")
    op.drop_table("integration_configs")
