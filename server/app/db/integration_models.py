"""
Integration Models - Database models for third-party integrations
Supports: Accounting, ERP, E-commerce sync
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.models import Base


class IntegrationProvider(str, Enum):
    """Supported integration providers"""

    # Accounting
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    FRESHBOOKS = "freshbooks"
    WAVE = "wave"

    # ERP
    SAP = "sap"
    ORACLE_NETSUITE = "oracle_netsuite"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"

    # E-commerce
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    ETSY = "etsy"
    AMAZON = "amazon"

    # Marketplace
    SQUARE = "square"
    CLOVER = "clover"


class SyncDirection(str, Enum):
    """Direction of data sync"""

    INBOUND = "inbound"  # Pull from external system
    OUTBOUND = "outbound"  # Push to external system
    BIDIRECTIONAL = "bidirectional"  # Two-way sync


class SyncType(str, Enum):
    """Type of data being synced"""

    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    PAYMENTS = "payments"
    ORDERS = "orders"


class SyncStatus(str, Enum):
    """Status of sync operation"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class IntegrationConfig(Base):
    """Stores configuration for third-party integrations"""

    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(SQLEnum(IntegrationProvider), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)

    # Authentication
    api_key = Column(String(512), nullable=False)  # Encrypted in practice
    api_secret = Column(String(512), nullable=True)  # Encrypted in practice
    webhook_url = Column(String(255), nullable=True)
    webhook_secret = Column(String(255), nullable=True)

    # Configuration
    sync_direction = Column(SQLEnum(SyncDirection), default=SyncDirection.BIDIRECTIONAL)
    sync_frequency = Column(Integer, default=3600)  # Seconds (default 1 hour)

    # Features
    sync_sales = Column(Boolean, default=True)
    sync_inventory = Column(Boolean, default=True)
    sync_customers = Column(Boolean, default=False)
    sync_products = Column(Boolean, default=False)
    sync_payments = Column(Boolean, default=False)

    # Status & Metadata
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(SQLEnum(SyncStatus), nullable=True)

    # Custom settings
    extra_config = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sync_logs = relationship(
        "IntegrationSyncLog", back_populates="config", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<IntegrationConfig(id={self.id}, provider={self.provider}, name={self.name})>"


class IntegrationSyncLog(Base):
    """Tracks all integration sync operations"""

    __tablename__ = "integration_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(
        Integer, ForeignKey("integration_configs.id"), nullable=False, index=True
    )

    sync_type = Column(SQLEnum(SyncType), nullable=False, index=True)
    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)

    # Record counts
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Sync details
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default=None)

    # Response data
    response_data = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    config = relationship("IntegrationConfig", back_populates="sync_logs")

    def __repr__(self):
        return f"<IntegrationSyncLog(id={self.id}, type={self.sync_type}, status={self.status})>"


class IntegrationMapping(Base):
    """Maps Vendly fields to external system fields"""

    __tablename__ = "integration_mappings"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(
        Integer, ForeignKey("integration_configs.id"), nullable=False, index=True
    )

    vendly_field = Column(String(255), nullable=False)  # e.g., "sale.total_amount"
    external_field = Column(
        String(255), nullable=False
    )  # e.g., "amount", "total_price"

    field_type = Column(String(50), default="string")  # string, number, date, boolean
    transformation = Column(Text, nullable=True)  # JSON transformation rule
    is_required = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IntegrationMapping(vendly={self.vendly_field}, external={self.external_field})>"


class IntegrationWebhook(Base):
    """Incoming webhooks from external systems"""

    __tablename__ = "integration_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(
        Integer, ForeignKey("integration_configs.id"), nullable=False, index=True
    )

    webhook_type = Column(
        String(100), nullable=False
    )  # e.g., "order.created", "product.updated"
    event_id = Column(String(255), nullable=False, unique=True)  # External event ID

    payload = Column(JSON, nullable=False)
    signature = Column(String(512), nullable=True)

    processed = Column(Boolean, default=False, index=True)
    processing_status = Column(SQLEnum(SyncStatus), nullable=True)
    processing_error = Column(Text, nullable=True)

    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<IntegrationWebhook(id={self.id}, type={self.webhook_type})>"
