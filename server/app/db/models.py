"""
Vendly POS - Database Models
=============================
MySQL/SQLite compatible models
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
        DateTime, default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sales")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="sales")
    items: Mapped[List["SaleItem"]] = relationship(
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
    percent = "percent"
    amount = "amount"


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

    # Index for quick lookups
    __table_args__ = ({"indexes": [{"columns": ["user_id", "is_active"]}]},)
