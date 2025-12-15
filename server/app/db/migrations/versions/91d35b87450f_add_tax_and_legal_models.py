"""Add tax and legal models

Revision ID: 91d35b87450f
Revises: 07e33e42fdb9
Create Date: 2025-12-15 15:12:13.606131

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '91d35b87450f'
down_revision: Union[str, None] = '07e33e42fdb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tax_rates table
    op.create_table('tax_rates',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('region', sa.String(length=10), nullable=False),
    sa.Column('tax_type', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('state_code', sa.String(length=10), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('effective_from', sa.DateTime(), nullable=False),
    sa.Column('effective_to', sa.DateTime(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_rates_is_active'), 'tax_rates', ['is_active'], unique=False)
    op.create_index(op.f('ix_tax_rates_region'), 'tax_rates', ['region'], unique=False)

    # Create legal_documents table
    op.create_table('legal_documents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('doc_type', sa.String(length=50), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('content_html', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('requires_acceptance', sa.Boolean(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_documents_doc_type'), 'legal_documents', ['doc_type'], unique=False)
    op.create_index(op.f('ix_legal_documents_is_active'), 'legal_documents', ['is_active'], unique=False)

    # Create tax_configurations table
    op.create_table('tax_configurations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('region', sa.String(length=10), nullable=False),
    sa.Column('tax_id', sa.String(length=50), nullable=True),
    sa.Column('is_tax_exempt', sa.Boolean(), nullable=False),
    sa.Column('default_tax_rate_id', sa.Integer(), nullable=True),
    sa.Column('enable_compound_tax', sa.Boolean(), nullable=False),
    sa.Column('enable_reverse_charge', sa.Boolean(), nullable=False),
    sa.Column('enable_tax_invoice', sa.Boolean(), nullable=False),
    sa.Column('rounding_method', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['default_tax_rate_id'], ['tax_rates.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_configurations_user_id'), 'tax_configurations', ['user_id'], unique=False)

    # Create legal_document_acceptances table
    op.create_table('legal_document_acceptances',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('legal_document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('accepted_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.ForeignKeyConstraint(['legal_document_id'], ['legal_documents.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_document_acceptances_accepted_at'), 'legal_document_acceptances', ['accepted_at'], unique=False)
    op.create_index(op.f('ix_legal_document_acceptances_customer_id'), 'legal_document_acceptances', ['customer_id'], unique=False)
    op.create_index(op.f('ix_legal_document_acceptances_legal_document_id'), 'legal_document_acceptances', ['legal_document_id'], unique=False)
    op.create_index(op.f('ix_legal_document_acceptances_user_id'), 'legal_document_acceptances', ['user_id'], unique=False)

    # Create tax_calculations table
    op.create_table('tax_calculations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sale_id', sa.Integer(), nullable=False),
    sa.Column('tax_rate_id', sa.Integer(), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('tax_type', sa.String(length=20), nullable=False),
    sa.Column('is_compound', sa.Boolean(), nullable=False),
    sa.Column('base_calculation_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['base_calculation_id'], ['tax_calculations.id'], ),
    sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
    sa.ForeignKeyConstraint(['tax_rate_id'], ['tax_rates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_calculations_sale_id'), 'tax_calculations', ['sale_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_tax_calculations_sale_id'), table_name='tax_calculations')
    op.drop_table('tax_calculations')
    
    op.drop_index(op.f('ix_legal_document_acceptances_user_id'), table_name='legal_document_acceptances')
    op.drop_index(op.f('ix_legal_document_acceptances_legal_document_id'), table_name='legal_document_acceptances')
    op.drop_index(op.f('ix_legal_document_acceptances_customer_id'), table_name='legal_document_acceptances')
    op.drop_index(op.f('ix_legal_document_acceptances_accepted_at'), table_name='legal_document_acceptances')
    op.drop_table('legal_document_acceptances')
    
    op.drop_index(op.f('ix_tax_configurations_user_id'), table_name='tax_configurations')
    op.drop_table('tax_configurations')
    
    op.drop_index(op.f('ix_legal_documents_is_active'), table_name='legal_documents')
    op.drop_index(op.f('ix_legal_documents_doc_type'), table_name='legal_documents')
    op.drop_table('legal_documents')
    
    op.drop_index(op.f('ix_tax_rates_region'), table_name='tax_rates')
    op.drop_index(op.f('ix_tax_rates_is_active'), table_name='tax_rates')
    op.drop_table('tax_rates')
