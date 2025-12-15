"""
Integration Router - REST API endpoints for third-party integrations
Handles: Accounting, ERP, E-commerce sync
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permission
from app.schemas.integrations import (
    IntegrationConfigCreate,
    IntegrationConfigResponse,
    IntegrationConfigUpdate,
    IntegrationHealthResponse,
    IntegrationMappingCreate,
    IntegrationMappingResponse,
    IntegrationProvider,
    IntegrationSyncLogResponse,
    ManualSyncRequest,
    ProviderInfo,
    SyncStatus,
    SyncStatusResponse,
    SyncType,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# ====================
# Provider Information
# ====================


@router.get("/providers", response_model=List[ProviderInfo])
def list_providers():
    """List all supported integration providers"""
    providers = [
        ProviderInfo(
            provider=IntegrationProvider.QUICKBOOKS,
            name="QuickBooks Online",
            category="accounting",
            description="Sync sales and inventory with QuickBooks",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.PRODUCTS,
                SyncType.CUSTOMERS,
            ],
            auth_type="oauth",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.XERO,
            name="Xero",
            category="accounting",
            description="Cloud accounting sync with Xero",
            supported_sync_types=[SyncType.SALES, SyncType.CUSTOMERS],
            auth_type="oauth",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.FRESHBOOKS,
            name="FreshBooks",
            category="accounting",
            description="Invoicing and expense sync",
            supported_sync_types=[SyncType.SALES, SyncType.CUSTOMERS],
            auth_type="api_key",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.SHOPIFY,
            name="Shopify",
            category="ecommerce",
            description="Sync orders and inventory with Shopify",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.INVENTORY,
                SyncType.PRODUCTS,
            ],
            auth_type="oauth",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.WOOCOMMERCE,
            name="WooCommerce",
            category="ecommerce",
            description="Sync WordPress/WooCommerce store",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.INVENTORY,
                SyncType.PRODUCTS,
            ],
            auth_type="api_key",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.MAGENTO,
            name="Magento",
            category="ecommerce",
            description="Enterprise ecommerce platform sync",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.INVENTORY,
                SyncType.PRODUCTS,
                SyncType.CUSTOMERS,
            ],
            auth_type="oauth",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.SQUARE,
            name="Square",
            category="marketplace",
            description="Point of sale and payment sync",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.INVENTORY,
                SyncType.PAYMENTS,
            ],
            auth_type="oauth",
            webhook_support=True,
        ),
        ProviderInfo(
            provider=IntegrationProvider.ORACLE_NETSUITE,
            name="Oracle NetSuite",
            category="erp",
            description="Enterprise resource planning integration",
            supported_sync_types=[
                SyncType.SALES,
                SyncType.INVENTORY,
                SyncType.PRODUCTS,
                SyncType.CUSTOMERS,
            ],
            auth_type="api_key",
            webhook_support=True,
        ),
    ]
    return providers


# ====================
# Integration Configuration
# ====================


@router.post(
    "/", response_model=IntegrationConfigResponse, status_code=status.HTTP_201_CREATED
)
def create_integration(
    provider: IntegrationProvider,
    config: IntegrationConfigCreate,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Create new integration config"""
    service = IntegrationService(db)
    new_config = service.create_integration(provider, config)
    return new_config


@router.get("/{config_id}", response_model=IntegrationConfigResponse)
def get_integration(
    config_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Get integration config details"""
    service = IntegrationService(db)
    config = service.get_integration(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return config


@router.get("", response_model=List[IntegrationConfigResponse])
def list_integrations(
    provider: Optional[IntegrationProvider] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List integrations with filters"""
    service = IntegrationService(db)
    configs = service.get_integrations(
        provider=provider,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return configs


@router.put("/{config_id}", response_model=IntegrationConfigResponse)
def update_integration(
    config_id: int,
    update_data: IntegrationConfigUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Update integration config"""
    service = IntegrationService(db)
    config = service.update_integration(config_id, update_data)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(
    config_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Delete integration config"""
    service = IntegrationService(db)
    if not service.delete_integration(config_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return None


# ====================
# Connection Testing
# ====================


@router.post("/{provider}/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    provider: IntegrationProvider,
    test_request: TestConnectionRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Test connection to external system"""
    service = IntegrationService(db)
    result = await service.test_connection(provider, test_request)
    return result


# ====================
# Manual Sync
# ====================


@router.post("/{config_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_sync(
    config_id: int,
    sync_request: ManualSyncRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Trigger manual sync for integration"""
    service = IntegrationService(db)
    result = await service.manual_sync(config_id, sync_request)
    if "error" in result and "Integration not found" in result["error"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return result


@router.post("/{config_id}/sync/{sync_type}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync_by_type(
    config_id: int,
    sync_type: SyncType,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dry_run: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Trigger sync for specific data type"""
    service = IntegrationService(db)
    sync_request = ManualSyncRequest(
        sync_type=sync_type,
        dry_run=dry_run,
    )
    result = await service.manual_sync(config_id, sync_request)
    if "error" in result and "Integration not found" in result["error"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return result


# ====================
# Sync Logs & Status
# ====================


@router.get("/{config_id}/logs", response_model=List[IntegrationSyncLogResponse])
def get_sync_logs(
    config_id: int,
    sync_type: Optional[SyncType] = None,
    status: Optional[SyncStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Get sync history for integration"""
    service = IntegrationService(db)
    config = service.get_integration(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    logs = service.get_sync_logs(config_id, sync_type, status, limit)
    return logs


@router.get("/{config_id}/status", response_model=SyncStatusResponse)
def get_sync_status(
    config_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Get sync status for integration"""
    service = IntegrationService(db)
    config = service.get_integration(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    stats = service.get_sync_statistics(config_id)
    return SyncStatusResponse(
        config_id=config_id,
        provider=config.provider.value,
        status=config.last_sync_status or SyncStatus.PENDING,
        last_sync_at=config.last_sync_at,
        last_sync_status=config.last_sync_status,
        total_syncs=stats["total_syncs"],
        successful_syncs=stats["successful_syncs"],
        failed_syncs=stats["failed_syncs"],
        pending_records=0,  # Would need to calculate from pending queue
    )


@router.get("/{config_id}/health", response_model=IntegrationHealthResponse)
async def get_integration_health(
    config_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Get integration health status"""
    service = IntegrationService(db)
    config = service.get_integration(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    return IntegrationHealthResponse(
        provider=config.provider.value,
        is_connected=config.is_verified,
        last_sync=config.last_sync_at,
        sync_status=config.last_sync_status or SyncStatus.PENDING,
    )


# ====================
# Field Mappings
# ====================


@router.post(
    "/{config_id}/mappings",
    response_model=IntegrationMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_field_mapping(
    config_id: int,
    mapping: IntegrationMappingCreate,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Create field mapping for integration"""
    service = IntegrationService(db)
    new_mapping = service.create_field_mapping(
        config_id,
        mapping.vendly_field,
        mapping.external_field,
        mapping.field_type,
        mapping.transformation,
    )
    if not new_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return new_mapping


@router.get("/{config_id}/mappings", response_model=List[IntegrationMappingResponse])
def get_field_mappings(
    config_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Get field mappings for integration"""
    service = IntegrationService(db)
    config = service.get_integration(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    mappings = service.get_field_mappings(config_id)
    return mappings


# ====================
# Webhooks
# ====================


@router.post("/{config_id}/webhooks", status_code=status.HTTP_200_OK)
def receive_webhook(
    config_id: int,
    webhook_data: dict,
    db: Session = Depends(get_db),
):
    """Receive webhook from external system (public endpoint - no auth required)"""
    service = IntegrationService(db)
    webhook = service.process_webhook(config_id, webhook_data)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )
    return {
        "success": webhook.processed,
        "webhook_id": webhook.id,
        "status": (
            webhook.processing_status.value if webhook.processing_status else None
        ),
    }
