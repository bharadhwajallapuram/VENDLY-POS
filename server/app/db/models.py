"""
Vendly POS - Database Models
=============================
MySQL/SQLite compatible models
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
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
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------- EST Timezone Helper ----------
# EST is UTC-5 (Eastern Standard Time)
EST = timezone(timedelta(hours=-5))


def now_est() -> datetime:
    """Return current time in EST timezone"""
    return datetime.now(EST).replace(tzinfo=None)


# ---------- Base ----------
class Base(DeclarativeBase):
    pass


# ---------- Enums ----------
class RoleEnum(str, PyEnum):
    clerk = "clerk"
    manager = "manager"
    admin = "admin"


class SaleStatus(str, PyEnum):
    open = "open"
    completed = "completed"
    voided = "voided"
    refunded = "refunded"


# ---------- Users ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="clerk", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    sales: Mapped[List["Sale"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ---------- Categories ----------
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    products: Mapped[List["Product"]] = relationship(back_populates="category")
    parent: Mapped[Optional["Category"]] = relationship(remote_side=[id])


# ---------- Products ----------
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    sale_items: Mapped[List["SaleItem"]] = relationship(back_populates="product")


# ---------- Customers ----------
class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    sales: Mapped[List["Sale"]] = relationship(back_populates="customer")


# ---------- Sales ----------
class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, nullable=False
    )  # total discount
    order_discount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, nullable=False
    )
    coupon_discount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, nullable=False
    )
    coupon_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_est, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sales")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="sales")
    items: Mapped[List["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )
    tax_calculations: Mapped[List["TaxCalculation"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    sale: Mapped["Sale"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="sale_items")


# ---------- Inventory Movements ----------
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    quantity_change: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # positive = in, negative = out
    movement_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sale, purchase, adjustment, return
    reference_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # sale_id or purchase_id
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )


# ---------- Coupons ----------
class CouponType(str, PyEnum):
    percentage = "percentage"
    fixed = "fixed"


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # percent or amount
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_off: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    min_order: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stackable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )


# ---------- Settings ----------
class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )


# ---------- Two-Factor Authentication ----------
class TwoFactorAuth(Base):
    __tablename__ = "two_factor_auth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    secret: Mapped[str] = mapped_column(String(32), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes: Mapped[str] = mapped_column(Text, nullable=True)  # Comma-separated
    enabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship()


# ---------- Backup Management ----------
class BackupJob(Base):
    """Scheduled backup jobs"""

    __tablename__ = "backup_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    backup_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sales, inventory, full
    schedule_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # daily, weekly, monthly, hourly
    schedule_time: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "02:00" for 2 AM
    retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # completed, failed, pending
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    logs: Mapped[List["BackupLog"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class BackupLog(Base):
    """Backup execution logs"""

    __tablename__ = "backup_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("backup_jobs.id"), nullable=True, index=True
    )
    backup_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    backup_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # pending, in_progress, completed, failed
    file_key: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Path in cloud storage
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Size in bytes
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )

    # Relationships
    job: Mapped[Optional["BackupJob"]] = relationship(back_populates="logs")


# ---------- Purchase Orders ----------
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, ordered, received, cancelled
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship()


# ---------- User Sessions ----------
class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_2fa_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    timeout_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship()


# ---------- Tax Configuration ----------
class TaxRegion(str, PyEnum):
    """Supported tax regions"""

    us = "us"  # US Sales Tax
    ca = "ca"  # Canada GST/HST
    uk = "uk"  # UK VAT
    eu = "eu"  # EU VAT
    au = "au"  # Australia GST
    in_ = "in"  # India GST
    sg = "sg"  # Singapore GST
    nz = "nz"  # New Zealand GST
    other = "other"  # Custom/Other


class TaxRate(Base):
    """Tax rates by region, category, and jurisdiction"""

    __tablename__ = "tax_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    tax_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # gst, vat, sales_tax
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "GST", "CGST", "SGST"
    rate: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # e.g., 18.0 for 18%
    state_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # e.g., "CA" for California
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class TaxConfiguration(Base):
    """Store-level tax configuration"""

    __tablename__ = "tax_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    region: Mapped[str] = mapped_column(String(10), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # GST ID, VAT ID, etc.
    is_tax_exempt: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_tax_rate_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tax_rates.id"), nullable=True
    )
    enable_compound_tax: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # For India GST
    enable_reverse_charge: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    enable_tax_invoice: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    rounding_method: Mapped[str] = mapped_column(
        String(20), default="round", nullable=False
    )  # round, truncate, ceiling
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    default_tax_rate: Mapped[Optional["TaxRate"]] = relationship(
        foreign_keys=[default_tax_rate_id]
    )


class TaxCalculation(Base):
    """Tax calculation history for reporting and audit"""

    __tablename__ = "tax_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id"), nullable=False, index=True
    )
    tax_rate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tax_rates.id"), nullable=False
    )
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    tax_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # gst, vat, sales_tax
    is_compound: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    base_calculation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tax_calculations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    sale: Mapped["Sale"] = relationship(back_populates="tax_calculations")
    tax_rate_ref: Mapped["TaxRate"] = relationship(foreign_keys=[tax_rate_id])


# ---------- Legal Documents ----------
class LegalDocumentType(str, PyEnum):
    """Types of legal documents"""

    privacy_policy = "privacy_policy"
    terms_of_service = "terms_of_service"
    return_policy = "return_policy"
    warranty_policy = "warranty_policy"
    cookie_policy = "cookie_policy"


class LegalDocument(Base):
    """Legal documents (privacy policy, terms, etc.) with versioning"""

    __tablename__ = "legal_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Rendered HTML version
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    requires_acceptance: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    acceptances: Mapped[List["LegalDocumentAcceptance"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class LegalDocumentAcceptance(Base):
    """Track acceptance of legal documents by users/customers"""

    __tablename__ = "legal_document_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    legal_document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal_documents.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Employee
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True, index=True
    )  # Customer
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["LegalDocument"] = relationship(back_populates="acceptances")
    user: Mapped[Optional["User"]] = relationship(foreign_keys=[user_id])
    customer: Mapped[Optional["Customer"]] = relationship(foreign_keys=[customer_id])


# ---------- Demand Forecasting ----------
class DemandHistory(Base):
    """Historical demand data for forecasting"""

    __tablename__ = "demand_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=True)  # 0-6
    is_weekend: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    product: Mapped["Product"] = relationship(foreign_keys=[product_id])

    # Indexes for efficient querying
    __table_args__ = (Index("ix_demand_history_product_date", "product_id", "date"),)


class DemandForecast(Base):
    """Demand forecast results"""

    __tablename__ = "demand_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    forecast_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    forecast_horizon_days: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    model_type: Mapped[str] = mapped_column(
        String(50), default="ensemble", nullable=False
    )  # prophet, arima, ensemble
    average_demand: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    min_forecast: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    max_forecast: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    confidence_level: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.95, nullable=False
    )
    mae: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # Mean Absolute Error
    rmse: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # Root Mean Squared Error
    r2_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # R² Score
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    # Relationships
    product: Mapped["Product"] = relationship(foreign_keys=[product_id])
    created_by: Mapped[Optional["User"]] = relationship(
        foreign_keys=[created_by_user_id]
    )
    forecast_details: Mapped[List["ForecastDetail"]] = relationship(
        back_populates="forecast", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_demand_forecast_product_date", "product_id", "forecast_date"),
    )


class ForecastDetail(Base):
    """Daily forecast details"""

    __tablename__ = "forecast_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    demand_forecast_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("demand_forecasts.id"), nullable=False, index=True
    )
    forecast_for_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    forecasted_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    lower_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    upper_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    actual_quantity: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    error: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    forecast: Mapped["DemandForecast"] = relationship(back_populates="forecast_details")

    # Indexes
    __table_args__ = (
        Index(
            "ix_forecast_detail_forecast_date",
            "demand_forecast_id",
            "forecast_for_date",
        ),
    )


class ForecastMetric(Base):
    """Aggregate forecast performance metrics"""

    __tablename__ = "forecast_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    metric_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mae: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Mean Absolute Error
    mape: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # Mean Absolute Percentage Error
    rmse: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Root Mean Squared Error
    r2: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # R² Score
    samples_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship(foreign_keys=[product_id])

    # Indexes
    __table_args__ = (
        Index("ix_forecast_metrics_product_date", "product_id", "metric_date"),
    )
