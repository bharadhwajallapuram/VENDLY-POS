"""add multistore and franchise tables

Revision ID: 004_multistore_franchise
Revises: subscription_001
Create Date: 2024-01-15

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '004_multistore_franchise'
down_revision = 'subscription_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Store Transfers table
    op.create_table(
        'store_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_number', sa.String(length=50), nullable=False),
        sa.Column('source_store_id', sa.Integer(), nullable=False),
        sa.Column('destination_store_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='normal'),
        sa.Column('requested_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('requested_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.Column('shipped_date', sa.DateTime(), nullable=True),
        sa.Column('received_date', sa.DateTime(), nullable=True),
        sa.Column('expected_arrival', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['source_store_id'], ['stores.id'], ),
        sa.ForeignKeyConstraint(['destination_store_id'], ['stores.id'], ),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transfer_number')
    )
    op.create_index('ix_store_transfers_transfer_number', 'store_transfers', ['transfer_number'])
    op.create_index('ix_store_transfers_status', 'store_transfers', ['status'])
    op.create_index('ix_store_transfers_source_store_id', 'store_transfers', ['source_store_id'])
    op.create_index('ix_store_transfers_destination_store_id', 'store_transfers', ['destination_store_id'])

    # Store Transfer Items table
    op.create_table(
        'store_transfer_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity_requested', sa.Integer(), nullable=False),
        sa.Column('quantity_sent', sa.Integer(), nullable=True),
        sa.Column('quantity_received', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['transfer_id'], ['store_transfers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_store_transfer_items_transfer_id', 'store_transfer_items', ['transfer_id'])

    # Transfer History table (audit log)
    op.create_table(
        'transfer_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('old_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=True),
        sa.Column('performed_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['transfer_id'], ['store_transfers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transfer_history_transfer_id', 'transfer_history', ['transfer_id'])

    # Franchise Fee Configuration table
    op.create_table(
        'franchise_fee_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('fee_type', sa.String(length=20), nullable=False, server_default='percentage'),
        sa.Column('calculation_type', sa.String(length=20), nullable=False, server_default='gross_sales'),
        sa.Column('rate', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('minimum_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('maximum_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('billing_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('grace_period_days', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('late_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_franchise_fee_configs_store_id', 'franchise_fee_configs', ['store_id'])

    # Franchise Fee Records table
    op.create_table(
        'franchise_fee_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('gross_sales', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('net_sales', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('calculated_fee', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('adjustments', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('final_fee', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('invoice_number', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['config_id'], ['franchise_fee_configs.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_franchise_fee_records_store_id', 'franchise_fee_records', ['store_id'])
    op.create_index('ix_franchise_fee_records_status', 'franchise_fee_records', ['status'])

    # Store Analytics Snapshots table
    op.create_table(
        'store_analytics_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_sales', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('transaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_ticket', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('gross_profit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('gross_margin', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('top_products', sa.JSON(), nullable=True),
        sa.Column('hourly_breakdown', sa.JSON(), nullable=True),
        sa.Column('category_breakdown', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('store_id', 'snapshot_date', name='uix_store_date_snapshot')
    )
    op.create_index('ix_store_analytics_snapshots_store_id', 'store_analytics_snapshots', ['store_id'])
    op.create_index('ix_store_analytics_snapshots_date', 'store_analytics_snapshots', ['snapshot_date'])

    # Store Inventory table (per-store inventory tracking)
    op.create_table(
        'store_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reserved_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_point', sa.Integer(), nullable=True),
        sa.Column('reorder_quantity', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('last_counted_at', sa.DateTime(), nullable=True),
        sa.Column('last_sold_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('store_id', 'product_id', name='uix_store_product_inventory')
    )
    op.create_index('ix_store_inventory_store_id', 'store_inventory', ['store_id'])
    op.create_index('ix_store_inventory_product_id', 'store_inventory', ['product_id'])

    # Integration Connections table
    op.create_table(
        'integration_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column('provider_account_id', sa.String(length=255), nullable=True),
        sa.Column('provider_account_name', sa.String(length=255), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_integration_connections_provider', 'integration_connections', ['provider'])
    op.create_index('ix_integration_connections_store_id', 'integration_connections', ['store_id'])


def downgrade() -> None:
    op.drop_table('integration_connections')
    op.drop_table('store_inventory')
    op.drop_table('store_analytics_snapshots')
    op.drop_table('franchise_fee_records')
    op.drop_table('franchise_fee_configs')
    op.drop_table('transfer_history')
    op.drop_table('store_transfer_items')
    op.drop_table('store_transfers')
