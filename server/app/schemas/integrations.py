"""
Integration Schemas - Pydantic models for integration API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


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

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


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


# ====================
# Integration Config Schemas
# ====================


class IntegrationConfigBase(BaseModel):
    """Base integration config"""

    provider: IntegrationProvider
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    api_key: str = Field(..., min_length=1)
    api_secret: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None

    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_frequency: int = Field(default=3600, ge=300, le=86400)  # 5 min to 24 hours

    sync_sales: bool = True
    sync_inventory: bool = True
    sync_customers: bool = False
    sync_products: bool = False
    sync_payments: bool = False

    is_active: bool = True
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class IntegrationConfigCreate(IntegrationConfigBase):
    """Schema for creating integration config"""

    pass


class IntegrationConfigUpdate(BaseModel):
    """Schema for updating integration config"""

    name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None

    sync_frequency: Optional[int] = None
    sync_sales: Optional[bool] = None
    sync_inventory: Optional[bool] = None
    sync_customers: Optional[bool] = None
    sync_products: Optional[bool] = None
    sync_payments: Optional[bool] = None

    is_active: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None


class IntegrationConfigResponse(IntegrationConfigBase):
    """Response schema for integration config"""

    id: int
    is_verified: bool
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[SyncStatus] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ====================
# Integration Sync Log Schemas
# ====================


class IntegrationSyncLogBase(BaseModel):
    """Base sync log"""

    sync_type: SyncType
    status: SyncStatus


class IntegrationSyncLogResponse(IntegrationSyncLogBase):
    """Response schema for sync log"""

    id: int
    config_id: int

    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int

    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    response_data: Dict[str, Any]

    created_at: datetime

    class Config:
        from_attributes = True


# ====================
# Integration Mapping Schemas
# ====================


class IntegrationMappingBase(BaseModel):
    """Base mapping"""

    vendly_field: str
    external_field: str
    field_type: str = "string"
    transformation: Optional[str] = None
    is_required: bool = False


class IntegrationMappingCreate(IntegrationMappingBase):
    """Schema for creating mapping"""

    pass


class IntegrationMappingResponse(IntegrationMappingBase):
    """Response schema for mapping"""

    id: int
    config_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================
# Integration Webhook Schemas
# ====================


class IntegrationWebhookReceive(BaseModel):
    """Schema for receiving webhook"""

    webhook_type: str
    event_id: str
    payload: Dict[str, Any]
    signature: Optional[str] = None


class IntegrationWebhookResponse(BaseModel):
    """Response schema for webhook"""

    id: int
    config_id: int
    webhook_type: str
    event_id: str

    processed: bool
    processing_status: Optional[SyncStatus] = None
    processing_error: Optional[str] = None

    received_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ====================
# Sync Trigger Schemas
# ====================


class ManualSyncRequest(BaseModel):
    """Request schema for manual sync"""

    sync_type: SyncType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dry_run: bool = False  # Simulate without committing


class SyncStatusResponse(BaseModel):
    """Response schema for sync status"""

    config_id: int
    provider: str
    status: SyncStatus
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[SyncStatus] = None

    total_syncs: int
    successful_syncs: int
    failed_syncs: int

    pending_records: int


# ====================
# Bulk Operations Schemas
# ====================


class SalesDataForSync(BaseModel):
    """Sales data for integration sync"""

    id: int
    date: datetime
    total_amount: float
    tax_amount: float
    discount_amount: float
    payment_method: str
    customer_id: Optional[int] = None
    items_count: int

    class Config:
        from_attributes = True


class InventoryDataForSync(BaseModel):
    """Inventory data for integration sync"""

    product_id: int
    product_name: str
    quantity_on_hand: int
    quantity_reserved: int
    reorder_point: int
    unit_price: float
    sku: str

    class Config:
        from_attributes = True


class CustomerDataForSync(BaseModel):
    """Customer data for integration sync"""

    id: int
    email: str
    phone: Optional[str] = None
    name: str
    total_purchases: float
    loyalty_points: int

    class Config:
        from_attributes = True


class BulkSyncRequest(BaseModel):
    """Request for bulk sync"""

    sync_type: SyncType
    records: List[Dict[str, Any]]
    dry_run: bool = False


class BulkSyncResponse(BaseModel):
    """Response for bulk sync"""

    config_id: int
    sync_type: SyncType
    total_records: int
    successful: int
    failed: int

    failed_records: List[Dict[str, Any]] = []
    errors: List[str] = []


# ====================
# Integration Status Schemas
# ====================


class ProviderInfo(BaseModel):
    """Information about a provider"""

    provider: IntegrationProvider
    name: str
    category: str  # accounting, erp, ecommerce
    description: str
    supported_sync_types: List[SyncType]
    auth_type: str  # oauth, api_key, both
    webhook_support: bool


class IntegrationHealthResponse(BaseModel):
    """Health check response"""

    provider: str
    is_connected: bool
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    sync_status: SyncStatus
    error_message: Optional[str] = None


# ====================
# Test Connection Schema
# ====================


class TestConnectionRequest(BaseModel):
    """Request to test integration connection"""

    api_key: str
    api_secret: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Response from connection test"""

    success: bool
    message: str
    provider: str
    api_accessible: bool
    webhook_accessible: Optional[bool] = None
    error_details: Optional[str] = None
