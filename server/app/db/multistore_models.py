"""
Vendly POS - Multi-Store & Franchise Models
============================================
Inter-store transfers, franchise fees, store analytics
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import Base


# ---------- Enums ----------
class TransferStatus(str, PyEnum):
    """Inter-store transfer status"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TransferPriority(str, PyEnum):
    """Transfer priority level"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class FranchiseFeeType(str, PyEnum):
    """Types of franchise fees"""
    ROYALTY = "royalty"  # Percentage of sales
    MARKETING = "marketing"  # Marketing fund contribution
    TECHNOLOGY = "technology"  # POS/tech fees
    INITIAL = "initial"  # Initial franchise fee
    RENEWAL = "renewal"  # Renewal fee
    OTHER = "other"


class FeeCalculationType(str, PyEnum):
    """How the fee is calculated"""
    PERCENTAGE = "percentage"  # % of gross sales
    FIXED = "fixed"  # Fixed monthly amount
    TIERED = "tiered"  # Tiered based on sales brackets
    PER_TRANSACTION = "per_transaction"  # Per transaction fee


# ---------- Inter-Store Transfers ----------
class StoreTransfer(Base):
    """Transfer inventory between stores"""
    __tablename__ = "store_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Transfer details
    transfer_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    from_store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    to_store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Status & Priority
    status: Mapped[str] = mapped_column(String(50), default=TransferStatus.PENDING.value)
    priority: Mapped[str] = mapped_column(String(20), default=TransferPriority.NORMAL.value)
    
    # Reason/Notes
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracking
    requested_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    received_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Dates
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Shipping info
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Totals (calculated from items)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0)
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    items: Mapped[List["StoreTransferItem"]] = relationship(back_populates="transfer", cascade="all, delete-orphan")
    history: Mapped[List["TransferHistory"]] = relationship(back_populates="transfer", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_transfer_tenant', 'tenant_id'),
        Index('ix_transfer_status', 'status'),
        Index('ix_transfer_from_store', 'from_store_id'),
        Index('ix_transfer_to_store', 'to_store_id'),
    )


class StoreTransferItem(Base):
    """Items in a transfer"""
    __tablename__ = "store_transfer_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(Integer, ForeignKey("store_transfers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Quantities
    quantity_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_sent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # May differ from requested
    quantity_received: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # May differ (damaged, etc.)
    
    # Value tracking
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    
    # Notes for discrepancies
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    transfer: Mapped["StoreTransfer"] = relationship(back_populates="items")

    __table_args__ = (
        Index('ix_transfer_item_transfer', 'transfer_id'),
        Index('ix_transfer_item_product', 'product_id'),
    )


class TransferHistory(Base):
    """Audit trail for transfers"""
    __tablename__ = "transfer_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(Integer, ForeignKey("store_transfers.id"), nullable=False)
    
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, approved, shipped, received, etc.
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    performed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    transfer: Mapped["StoreTransfer"] = relationship(back_populates="history")

    __table_args__ = (
        Index('ix_transfer_history_transfer', 'transfer_id'),
    )


# ---------- Franchise Fees ----------
class FranchiseFeeConfig(Base):
    """Configure franchise fee structure for a tenant"""
    __tablename__ = "franchise_fee_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Fee type and calculation
    fee_type: Mapped[str] = mapped_column(String(50), nullable=False)  # royalty, marketing, etc.
    calculation_type: Mapped[str] = mapped_column(String(50), default=FeeCalculationType.PERCENTAGE.value)
    
    # Amounts
    rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)  # For percentage (e.g., 0.05 = 5%)
    fixed_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)  # For fixed fees
    min_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)  # Minimum fee
    max_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)  # Cap
    
    # Tiered brackets (JSON): [{"min": 0, "max": 10000, "rate": 0.06}, ...]
    tier_brackets: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Schedule
    billing_day: Mapped[int] = mapped_column(Integer, default=1)  # Day of month to calculate
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Effective dates
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    effective_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    __table_args__ = (
        Index('ix_franchise_fee_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'fee_type', name='uq_tenant_fee_type'),
    )


class FranchiseFeeRecord(Base):
    """Actual franchise fee charges/payments"""
    __tablename__ = "franchise_fee_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    store_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("stores.id"), nullable=True)  # If per-store
    config_id: Mapped[int] = mapped_column(Integer, ForeignKey("franchise_fee_configs.id"), nullable=False)
    
    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Calculation basis
    gross_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Fee amounts
    calculated_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    adjustments: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    final_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    
    # Payment status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, invoiced, paid, overdue
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Link to invoice
    invoice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    __table_args__ = (
        Index('ix_fee_record_tenant', 'tenant_id'),
        Index('ix_fee_record_period', 'period_start', 'period_end'),
        Index('ix_fee_record_status', 'status'),
    )


# ---------- Store Analytics Snapshots ----------
class StoreAnalyticsSnapshot(Base):
    """Daily/weekly store performance snapshots for comparison"""
    __tablename__ = "store_analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Period
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily, weekly, monthly
    
    # Sales metrics
    gross_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    net_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_transaction_value: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    items_sold: Mapped[int] = mapped_column(Integer, default=0)
    
    # Customer metrics
    unique_customers: Mapped[int] = mapped_column(Integer, default=0)
    new_customers: Mapped[int] = mapped_column(Integer, default=0)
    returning_customers: Mapped[int] = mapped_column(Integer, default=0)
    
    # Inventory metrics
    total_inventory_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    low_stock_items: Mapped[int] = mapped_column(Integer, default=0)
    out_of_stock_items: Mapped[int] = mapped_column(Integer, default=0)
    inventory_turnover: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00)
    
    # Staff metrics
    staff_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0.00)
    sales_per_labor_hour: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    
    # Returns & refunds
    refund_count: Mapped[int] = mapped_column(Integer, default=0)
    refund_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    
    # Discounts
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('ix_analytics_tenant_store', 'tenant_id', 'store_id'),
        Index('ix_analytics_date', 'snapshot_date'),
        UniqueConstraint('store_id', 'snapshot_date', 'period_type', name='uq_store_snapshot'),
    )


# ---------- Store Inventory Levels ----------
class StoreInventory(Base):
    """Track inventory per store (for multi-store setups)"""
    __tablename__ = "store_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)  # In pending transfers
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)  # quantity - reserved
    
    # Par levels for this store
    min_quantity: Mapped[int] = mapped_column(Integer, default=0)
    max_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last activity
    last_sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_counted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('store_id', 'product_id', name='uq_store_product_inventory'),
        Index('ix_store_inventory_store', 'store_id'),
        Index('ix_store_inventory_product', 'product_id'),
    )
