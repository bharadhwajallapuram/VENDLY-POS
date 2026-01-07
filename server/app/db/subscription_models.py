"""
Vendly POS - Subscription & Multi-Tenant Models
=================================================
SaaS billing and multi-store support
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
class PlanTier(str, PyEnum):
    """Subscription plan tiers"""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, PyEnum):
    """Subscription status"""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class BillingInterval(str, PyEnum):
    """Billing interval"""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class InvoiceStatus(str, PyEnum):
    """Invoice status"""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


# ---------- Plans ----------
class Plan(Base):
    """Subscription plans configuration"""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PlanTier.FREE.value
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    price_monthly: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    price_yearly: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Stripe Price IDs
    stripe_price_monthly_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    stripe_price_yearly_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    stripe_product_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Limits
    max_stores: Mapped[int] = mapped_column(Integer, default=1)
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    max_products: Mapped[int] = mapped_column(Integer, default=100)
    max_transactions_monthly: Mapped[int] = mapped_column(Integer, default=500)

    # Features (JSON-like flags)
    feature_inventory: Mapped[bool] = mapped_column(Boolean, default=True)
    feature_reports: Mapped[bool] = mapped_column(Boolean, default=True)
    feature_advanced_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_custom_branding: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_priority_support: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_ai_insights: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_multi_store: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_integrations: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Show on pricing page
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="plan")


# ---------- Tenants (Organizations) ----------
class Tenant(Base):
    """Multi-tenant organization"""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # Contact Info
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Business Info
    business_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="US")

    # Stripe Customer
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    # Relationships
    stores: Mapped[List["Store"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    tenant_users: Mapped[List["TenantUser"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


# ---------- Stores ----------
class Store(Base):
    """Individual store/location within a tenant"""

    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Short code like "STORE01"

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="US")

    # Settings
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Override tenant timezone
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="stores")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_store_tenant_code"),
        Index("ix_store_tenant", "tenant_id"),
    )


# ---------- Tenant Users (User-Tenant Association) ----------
class TenantUser(Base):
    """Links users to tenants with roles"""

    __tablename__ = "tenant_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Role within this tenant
    role: Mapped[str] = mapped_column(
        String(50), default="member"
    )  # owner, admin, manager, member

    # Store access (null = all stores)
    store_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array of store IDs

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="tenant_users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
        Index("ix_tenant_user_tenant", "tenant_id"),
        Index("ix_tenant_user_user", "user_id"),
    )


# ---------- Subscriptions ----------
class Subscription(Base):
    """Tenant subscription to a plan"""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id"), nullable=False
    )

    # Stripe
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=SubscriptionStatus.TRIALING.value
    )
    billing_interval: Mapped[str] = mapped_column(
        String(20), default=BillingInterval.MONTHLY.value
    )

    # Dates
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    # Usage tracking
    transactions_this_month: Mapped[int] = mapped_column(Integer, default=0)
    usage_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")


# ---------- Invoices ----------
class Invoice(Base):
    """Billing invoices"""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Stripe
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Details
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=InvoiceStatus.DRAFT.value)

    # Amounts
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    amount_due: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Dates
    invoice_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # PDF
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="invoices")


# ---------- Usage Events (for metered billing) ----------
class UsageEvent(Base):
    """Track usage for metered billing"""

    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False, index=True
    )
    store_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("stores.id"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # transaction, api_call, etc.
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Metadata
    event_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_usage_tenant_type", "tenant_id", "event_type"),
        Index("ix_usage_created", "created_at"),
    )
