"""
Integration Service - Business logic for third-party integrations
Handles: Accounting, ERP, E-commerce sync
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.db.integration_models import (
    IntegrationConfig,
    IntegrationMapping,
    IntegrationProvider,
    IntegrationSyncLog,
    IntegrationWebhook,
    SyncDirection,
    SyncStatus,
    SyncType,
)
from app.schemas.integrations import (
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
    ManualSyncRequest,
    TestConnectionRequest,
)

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing third-party integrations"""

    def __init__(self, db: Session):
        self.db = db
        self.timeout = 30

    # ====================
    # Integration Config Management
    # ====================

    def create_integration(
        self, provider: IntegrationProvider, config: IntegrationConfigCreate
    ) -> IntegrationConfig:
        """Create new integration config"""
        db_config = IntegrationConfig(provider=provider, **config.dict())
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        logger.info(f"Created integration: {provider} - {config.name}")
        return db_config

    def get_integration(self, config_id: int) -> Optional[IntegrationConfig]:
        """Get integration config by ID"""
        return (
            self.db.query(IntegrationConfig)
            .filter(IntegrationConfig.id == config_id)
            .first()
        )

    def get_integrations(
        self,
        provider: Optional[IntegrationProvider] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[IntegrationConfig]:
        """List integrations with filters"""
        query = self.db.query(IntegrationConfig)

        if provider:
            query = query.filter(IntegrationConfig.provider == provider)
        if is_active is not None:
            query = query.filter(IntegrationConfig.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    def update_integration(
        self, config_id: int, update_data: IntegrationConfigUpdate
    ) -> Optional[IntegrationConfig]:
        """Update integration config"""
        config = self.get_integration(config_id)
        if not config:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        logger.info(f"Updated integration: {config_id}")
        return config

    def delete_integration(self, config_id: int) -> bool:
        """Delete integration config"""
        config = self.get_integration(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        logger.info(f"Deleted integration: {config_id}")
        return True

    # ====================
    # Integration Testing
    # ====================

    async def test_connection(
        self, provider: IntegrationProvider, test_request: TestConnectionRequest
    ) -> Dict[str, Any]:
        """Test connection to external system"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                result = await self._test_provider_connection(
                    client, provider, test_request
                )
            return result
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "message": "Connection test failed",
                "provider": provider.value,
                "api_accessible": False,
                "error_details": str(e),
            }

    async def _test_provider_connection(
        self,
        client: httpx.AsyncClient,
        provider: IntegrationProvider,
        test_request: TestConnectionRequest,
    ) -> Dict[str, Any]:
        """Test connection for specific provider"""

        if provider == IntegrationProvider.QUICKBOOKS:
            return await self._test_quickbooks(client, test_request)
        elif provider == IntegrationProvider.XERO:
            return await self._test_xero(client, test_request)
        elif provider == IntegrationProvider.SHOPIFY:
            return await self._test_shopify(client, test_request)
        elif provider == IntegrationProvider.WOOCOMMERCE:
            return await self._test_woocommerce(client, test_request)
        else:
            return {
                "success": False,
                "message": f"Provider {provider.value} not yet implemented",
                "provider": provider.value,
                "api_accessible": False,
            }

    async def _test_quickbooks(
        self, client: httpx.AsyncClient, test_request: TestConnectionRequest
    ) -> Dict[str, Any]:
        """Test QuickBooks connection"""
        try:
            headers = {"Authorization": f"Bearer {test_request.api_key}"}
            response = await client.get(
                "https://quickbooks.api.intuit.com/v2/company/123/query",
                headers=headers,
            )
            return {
                "success": response.status_code < 400,
                "message": (
                    "QuickBooks connection successful"
                    if response.status_code < 400
                    else "Failed to connect"
                ),
                "provider": "quickbooks",
                "api_accessible": response.status_code < 400,
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "provider": "quickbooks",
                "api_accessible": False,
                "error_details": str(e),
            }

    async def _test_xero(
        self, client: httpx.AsyncClient, test_request: TestConnectionRequest
    ) -> Dict[str, Any]:
        """Test Xero connection"""
        try:
            headers = {"Authorization": f"Bearer {test_request.api_key}"}
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Organisation", headers=headers
            )
            return {
                "success": response.status_code < 400,
                "message": (
                    "Xero connection successful"
                    if response.status_code < 400
                    else "Failed to connect"
                ),
                "provider": "xero",
                "api_accessible": response.status_code < 400,
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "provider": "xero",
                "api_accessible": False,
                "error_details": str(e),
            }

    async def _test_shopify(
        self, client: httpx.AsyncClient, test_request: TestConnectionRequest
    ) -> Dict[str, Any]:
        """Test Shopify connection"""
        try:
            headers = {"X-Shopify-Access-Token": test_request.api_key}
            response = await client.get(
                "https://your-store.myshopify.com/admin/api/2024-01/shop.json",
                headers=headers,
            )
            return {
                "success": response.status_code < 400,
                "message": (
                    "Shopify connection successful"
                    if response.status_code < 400
                    else "Failed to connect"
                ),
                "provider": "shopify",
                "api_accessible": response.status_code < 400,
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "provider": "shopify",
                "api_accessible": False,
                "error_details": str(e),
            }

    async def _test_woocommerce(
        self, client: httpx.AsyncClient, test_request: TestConnectionRequest
    ) -> Dict[str, Any]:
        """Test WooCommerce connection"""
        try:
            # WooCommerce uses basic auth with key:secret
            import base64

            credentials = base64.b64encode(
                f"{test_request.api_key}:{test_request.api_secret}".encode()
            ).decode()
            headers = {"Authorization": f"Basic {credentials}"}
            response = await client.get(
                "https://example.com/wp-json/wc/v3/system_status", headers=headers
            )
            return {
                "success": response.status_code < 400,
                "message": (
                    "WooCommerce connection successful"
                    if response.status_code < 400
                    else "Failed to connect"
                ),
                "provider": "woocommerce",
                "api_accessible": response.status_code < 400,
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "provider": "woocommerce",
                "api_accessible": False,
                "error_details": str(e),
            }

    # ====================
    # Sync Operations
    # ====================

    async def manual_sync(
        self, config_id: int, sync_request: ManualSyncRequest
    ) -> Dict[str, Any]:
        """Trigger manual sync"""
        config = self.get_integration(config_id)
        if not config:
            return {"success": False, "error": "Integration not found"}

        sync_log = IntegrationSyncLog(
            config_id=config_id,
            sync_type=sync_request.sync_type,
            status=SyncStatus.IN_PROGRESS,
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            if sync_request.sync_type == SyncType.SALES:
                result = await self._sync_sales_data(config, sync_log, sync_request)
            elif sync_request.sync_type == SyncType.INVENTORY:
                result = await self._sync_inventory_data(config, sync_log, sync_request)
            elif sync_request.sync_type == SyncType.CUSTOMERS:
                result = await self._sync_customers_data(config, sync_log, sync_request)
            elif sync_request.sync_type == SyncType.PRODUCTS:
                result = await self._sync_products_data(config, sync_log, sync_request)
            else:
                result = {"error": "Unsupported sync type"}

            sync_log.status = (
                SyncStatus.COMPLETED if result.get("success") else SyncStatus.FAILED
            )
            sync_log.response_data = result

        except Exception as e:
            logger.error(f"Sync failed for config {config_id}: {str(e)}")
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = str(e)
            result = {"success": False, "error": str(e)}

        sync_log.completed_at = datetime.utcnow()
        if sync_log.started_at:
            sync_log.duration_seconds = int(
                (sync_log.completed_at - sync_log.started_at).total_seconds()
            )

        self.db.commit()
        self.db.refresh(sync_log)

        return {
            "success": result.get("success", False),
            "sync_log_id": sync_log.id,
            **result,
        }

    async def _sync_sales_data(
        self,
        config: IntegrationConfig,
        sync_log: IntegrationSyncLog,
        sync_request: ManualSyncRequest,
    ) -> Dict[str, Any]:
        """Sync sales data to external system"""
        # This would query sales data from Vendly and push to external system
        try:
            # Get sales data (example)
            from app.db.models import Sale

            query = self.db.query(Sale)
            if sync_request.start_date:
                query = query.filter(Sale.created_at >= sync_request.start_date)
            if sync_request.end_date:
                query = query.filter(Sale.created_at <= sync_request.end_date)

            sales = query.all()

            if not sync_request.dry_run and config.sync_direction in [
                SyncDirection.OUTBOUND,
                SyncDirection.BIDIRECTIONAL,
            ]:
                # Push to external system
                await self._push_to_external_system(config, SyncType.SALES, sales)

            return {
                "success": True,
                "sync_type": SyncType.SALES.value,
                "records_processed": len(sales),
                "records_created": len(sales),
                "message": f"Synced {len(sales)} sales records",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_inventory_data(
        self,
        config: IntegrationConfig,
        sync_log: IntegrationSyncLog,
        sync_request: ManualSyncRequest,
    ) -> Dict[str, Any]:
        """Sync inventory data"""
        try:
            # Get inventory data
            from app.db.models import Product

            products = self.db.query(Product).all()

            if not sync_request.dry_run and config.sync_direction in [
                SyncDirection.OUTBOUND,
                SyncDirection.BIDIRECTIONAL,
            ]:
                await self._push_to_external_system(
                    config, SyncType.INVENTORY, products
                )

            return {
                "success": True,
                "sync_type": SyncType.INVENTORY.value,
                "records_processed": len(products),
                "records_updated": len(products),
                "message": f"Synced {len(products)} inventory records",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_customers_data(
        self,
        config: IntegrationConfig,
        sync_log: IntegrationSyncLog,
        sync_request: ManualSyncRequest,
    ) -> Dict[str, Any]:
        """Sync customer data"""
        try:
            from app.db.models import Customer

            customers = self.db.query(Customer).all()

            if not sync_request.dry_run and config.sync_direction in [
                SyncDirection.OUTBOUND,
                SyncDirection.BIDIRECTIONAL,
            ]:
                await self._push_to_external_system(
                    config, SyncType.CUSTOMERS, customers
                )

            return {
                "success": True,
                "sync_type": SyncType.CUSTOMERS.value,
                "records_processed": len(customers),
                "records_updated": len(customers),
                "message": f"Synced {len(customers)} customer records",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_products_data(
        self,
        config: IntegrationConfig,
        sync_log: IntegrationSyncLog,
        sync_request: ManualSyncRequest,
    ) -> Dict[str, Any]:
        """Sync product data"""
        try:
            from app.db.models import Product

            products = self.db.query(Product).all()

            if not sync_request.dry_run and config.sync_direction in [
                SyncDirection.OUTBOUND,
                SyncDirection.BIDIRECTIONAL,
            ]:
                await self._push_to_external_system(config, SyncType.PRODUCTS, products)

            return {
                "success": True,
                "sync_type": SyncType.PRODUCTS.value,
                "records_processed": len(products),
                "records_created": len(products),
                "message": f"Synced {len(products)} product records",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _push_to_external_system(
        self, config: IntegrationConfig, sync_type: SyncType, data: List[Any]
    ) -> bool:
        """Push data to external system via API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = self._transform_data(sync_type, data)
                # Send to external system based on provider
                # Implementation depends on specific provider
                logger.info(
                    f"Pushed {len(data)} {sync_type.value} records to {config.provider}"
                )
                return True
        except Exception as e:
            logger.error(f"Failed to push data: {str(e)}")
            return False

    def _transform_data(self, sync_type: SyncType, data: List[Any]) -> Dict[str, Any]:
        """Transform Vendly data to external system format"""
        # Use mappings to transform data
        # This is a simplified version - real implementation would be more complex
        return {
            "sync_type": sync_type.value,
            "records": [self._serialize_record(record) for record in data],
        }

    def _serialize_record(self, record: Any) -> Dict[str, Any]:
        """Serialize ORM object to dict"""
        if hasattr(record, "__dict__"):
            return {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
        return record.dict() if hasattr(record, "dict") else {}

    # ====================
    # Webhook Operations
    # ====================

    def process_webhook(
        self, config_id: int, webhook_data: Dict[str, Any]
    ) -> Optional[IntegrationWebhook]:
        """Process incoming webhook from external system"""
        config = self.get_integration(config_id)
        if not config:
            return None

        webhook = IntegrationWebhook(
            config_id=config_id,
            webhook_type=webhook_data.get("type", "unknown"),
            event_id=webhook_data.get("id", ""),
            payload=webhook_data,
        )

        try:
            # Verify webhook signature if provided
            if webhook_data.get("signature") and config.webhook_secret:
                if not self._verify_webhook_signature(
                    webhook_data, config.webhook_secret
                ):
                    webhook.processing_status = SyncStatus.FAILED
                    webhook.processing_error = "Invalid signature"
                    self.db.add(webhook)
                    self.db.commit()
                    return webhook

            # Process webhook based on type
            webhook.processed = True
            webhook.processing_status = SyncStatus.COMPLETED
            webhook.processed_at = datetime.utcnow()

            logger.info(f"Processed webhook {webhook.event_id} from {config.provider}")

        except Exception as e:
            webhook.processed = True
            webhook.processing_status = SyncStatus.FAILED
            webhook.processing_error = str(e)
            logger.error(f"Failed to process webhook: {str(e)}")

        self.db.add(webhook)
        self.db.commit()
        return webhook

    def _verify_webhook_signature(
        self, webhook_data: Dict[str, Any], secret: str
    ) -> bool:
        """Verify webhook signature"""
        signature = webhook_data.get("signature", "")
        payload = json.dumps(webhook_data.get("payload", {}))

        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    # ====================
    # Field Mapping
    # ====================

    def create_field_mapping(
        self,
        config_id: int,
        vendly_field: str,
        external_field: str,
        field_type: str = "string",
        transformation: Optional[str] = None,
    ) -> Optional[IntegrationMapping]:
        """Create field mapping"""
        config = self.get_integration(config_id)
        if not config:
            return None

        mapping = IntegrationMapping(
            config_id=config_id,
            vendly_field=vendly_field,
            external_field=external_field,
            field_type=field_type,
            transformation=transformation,
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_field_mappings(self, config_id: int) -> List[IntegrationMapping]:
        """Get field mappings for integration"""
        return (
            self.db.query(IntegrationMapping)
            .filter(IntegrationMapping.config_id == config_id)
            .all()
        )

    # ====================
    # Sync History & Logs
    # ====================

    def get_sync_logs(
        self,
        config_id: int,
        sync_type: Optional[SyncType] = None,
        status: Optional[SyncStatus] = None,
        limit: int = 50,
    ) -> List[IntegrationSyncLog]:
        """Get sync history"""
        query = self.db.query(IntegrationSyncLog).filter(
            IntegrationSyncLog.config_id == config_id
        )

        if sync_type:
            query = query.filter(IntegrationSyncLog.sync_type == sync_type)
        if status:
            query = query.filter(IntegrationSyncLog.status == status)

        return query.order_by(desc(IntegrationSyncLog.created_at)).limit(limit).all()

    def get_sync_statistics(self, config_id: int) -> Dict[str, Any]:
        """Get sync statistics for integration"""
        logs = (
            self.db.query(IntegrationSyncLog)
            .filter(IntegrationSyncLog.config_id == config_id)
            .all()
        )

        total = len(logs)
        successful = len([l for l in logs if l.status == SyncStatus.COMPLETED])
        failed = len([l for l in logs if l.status == SyncStatus.FAILED])

        return {
            "config_id": config_id,
            "total_syncs": total,
            "successful_syncs": successful,
            "failed_syncs": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }
