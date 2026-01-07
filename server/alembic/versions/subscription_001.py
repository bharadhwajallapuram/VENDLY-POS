"""Create subscription and multi-tenant tables

Revision ID: subscription_001
Revises: integration_001
Create Date: 2024-12-30 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "subscription_001"
down_revision = "integration_001"
branch_labels = None
depends_on = None


def upgrade():
    # Create plans table
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False, server_default="starter"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("stripe_price_id_monthly", sa.String(100), nullable=True),
        sa.Column("stripe_price_id_yearly", sa.String(100), nullable=True),
        sa.Column("max_stores", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_products", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "max_transactions_monthly",
            sa.Integer(),
            nullable=False,
            server_default="1000",
        ),
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_plans_tier", "plans", ["tier"])

    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("business_type", sa.String(100), nullable=True),
        sa.Column("tax_id", sa.String(100), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(3), nullable=False, server_default="US"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("locale", sa.String(10), nullable=False, server_default="en-US"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True),
        sa.Column("stripe_customer_id", sa.String(100), nullable=True),
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_tenants_email", "tenants", ["email"])
    op.create_index("ix_tenants_stripe_customer_id", "tenants", ["stripe_customer_id"])

    # Create stores table
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(3), nullable=False, server_default="US"),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_stores_tenant_id", "stores", ["tenant_id"])
    op.create_index("ix_stores_code", "stores", ["code"])

    # Create tenant_users table
    op.create_table(
        "tenant_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column(
            "permissions", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("invited_at", sa.DateTime(), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
    )
    op.create_index("ix_tenant_users_tenant_id", "tenant_users", ["tenant_id"])
    op.create_index("ix_tenant_users_user_id", "tenant_users", ["user_id"])

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(100), nullable=True),
        sa.Column("stripe_customer_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="trialing"),
        sa.Column(
            "billing_interval", sa.String(20), nullable=False, server_default="monthly"
        ),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column(
            "cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.Column("trial_start", sa.DateTime(), nullable=True),
        sa.Column("trial_end", sa.DateTime(), nullable=True),
        sa.Column(
            "transactions_this_month", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("usage_reset_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index(
        "ix_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
    )
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("stripe_invoice_id", sa.String(100), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(100), nullable=True),
        sa.Column("number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("invoice_pdf_url", sa.String(500), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(500), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("period_start", sa.DateTime(), nullable=True),
        sa.Column("period_end", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_stripe_invoice_id", "invoices", ["stripe_invoice_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    # Create usage_events table
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "event_metadata", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_usage_events_tenant_id", "usage_events", ["tenant_id"])
    op.create_index("ix_usage_events_event_type", "usage_events", ["event_type"])
    op.create_index("ix_usage_events_recorded_at", "usage_events", ["recorded_at"])


def downgrade():
    op.drop_table("usage_events")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("tenant_users")
    op.drop_table("stores")
    op.drop_table("tenants")
    op.drop_table("plans")

    # Drop enums if needed (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS billinginterval CASCADE")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS invoicestatus CASCADE")
