"""
Vendly POS - OAuth Integration Service
=======================================
QuickBooks, Shopify, and other OAuth2 integrations
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.db.integration_models import (
    IntegrationConfig,
    IntegrationProvider,
    SyncDirection,
)

logger = logging.getLogger(__name__)


# ============================================
# OAuth Configuration
# ============================================

OAUTH_CONFIGS = {
    IntegrationProvider.QUICKBOOKS: {
        "auth_url": "https://appcenter.intuit.com/connect/oauth2",
        "token_url": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        "api_base": "https://quickbooks.api.intuit.com/v3",
        "scopes": ["com.intuit.quickbooks.accounting"],
        "env_client_id": "QUICKBOOKS_CLIENT_ID",
        "env_client_secret": "QUICKBOOKS_CLIENT_SECRET",
    },
    IntegrationProvider.XERO: {
        "auth_url": "https://login.xero.com/identity/connect/authorize",
        "token_url": "https://identity.xero.com/connect/token",
        "api_base": "https://api.xero.com/api.xro/2.0",
        "scopes": ["openid", "profile", "email", "accounting.transactions", "accounting.settings"],
        "env_client_id": "XERO_CLIENT_ID",
        "env_client_secret": "XERO_CLIENT_SECRET",
    },
    IntegrationProvider.SHOPIFY: {
        "auth_url": "https://{shop}.myshopify.com/admin/oauth/authorize",
        "token_url": "https://{shop}.myshopify.com/admin/oauth/access_token",
        "api_base": "https://{shop}.myshopify.com/admin/api/2024-01",
        "scopes": ["read_products", "write_products", "read_orders", "read_inventory", "write_inventory"],
        "env_client_id": "SHOPIFY_CLIENT_ID",
        "env_client_secret": "SHOPIFY_CLIENT_SECRET",
    },
    IntegrationProvider.SQUARE: {
        "auth_url": "https://connect.squareup.com/oauth2/authorize",
        "token_url": "https://connect.squareup.com/oauth2/token",
        "api_base": "https://connect.squareup.com/v2",
        "scopes": ["ITEMS_READ", "ITEMS_WRITE", "ORDERS_READ", "INVENTORY_READ", "INVENTORY_WRITE"],
        "env_client_id": "SQUARE_CLIENT_ID",
        "env_client_secret": "SQUARE_CLIENT_SECRET",
    },
}


class OAuthService:
    """Service for handling OAuth2 flows"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_auth_url(
        self,
        provider: IntegrationProvider,
        redirect_uri: str,
        tenant_id: int,
        store_id: Optional[int] = None,
        shop_domain: Optional[str] = None,  # For Shopify
    ) -> Dict[str, str]:
        """Generate OAuth authorization URL"""
        config = OAUTH_CONFIGS.get(provider)
        if not config:
            raise ValueError(f"Unsupported provider: {provider}")
        
        client_id = os.getenv(config["env_client_id"])
        if not client_id:
            raise ValueError(f"Missing {config['env_client_id']} environment variable")
        
        # Generate state token for CSRF protection
        state_data = {
            "tenant_id": tenant_id,
            "store_id": store_id,
            "provider": provider.value,
            "nonce": secrets.token_urlsafe(16),
        }
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # Build auth URL
        auth_url = config["auth_url"]
        if provider == IntegrationProvider.SHOPIFY and shop_domain:
            auth_url = auth_url.format(shop=shop_domain)
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
        }
        
        # Provider-specific params
        if provider == IntegrationProvider.QUICKBOOKS:
            params["response_mode"] = "query"
        elif provider == IntegrationProvider.XERO:
            params["response_mode"] = "query"
        
        full_url = f"{auth_url}?{urlencode(params)}"
        
        return {
            "auth_url": full_url,
            "state": state,
        }
    
    async def exchange_code(
        self,
        provider: IntegrationProvider,
        code: str,
        redirect_uri: str,
        state: str,
        shop_domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        config = OAUTH_CONFIGS.get(provider)
        if not config:
            raise ValueError(f"Unsupported provider: {provider}")
        
        client_id = os.getenv(config["env_client_id"])
        client_secret = os.getenv(config["env_client_secret"])
        
        if not client_id or not client_secret:
            raise ValueError(f"Missing OAuth credentials for {provider}")
        
        # Decode state
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state))
        except Exception:
            raise ValueError("Invalid state parameter")
        
        # Build token URL
        token_url = config["token_url"]
        if provider == IntegrationProvider.SHOPIFY and shop_domain:
            token_url = token_url.format(shop=shop_domain)
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            if provider == IntegrationProvider.QUICKBOOKS:
                # QuickBooks uses Basic auth
                auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                response = await client.post(
                    token_url,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                )
            elif provider == IntegrationProvider.SHOPIFY:
                # Shopify uses simple POST
                response = await client.post(
                    token_url,
                    json={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                    },
                )
            else:
                # Standard OAuth2
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise ValueError(f"Token exchange failed: {response.status_code}")
        
        token_data = response.json()
        
        # Save connection
        connection = await self._save_connection(
            provider=provider,
            tenant_id=state_data["tenant_id"],
            store_id=state_data.get("store_id"),
            token_data=token_data,
            shop_domain=shop_domain,
        )
        
        return {
            "connection_id": connection.id,
            "provider": provider.value,
            "status": "connected",
        }
    
    async def _save_connection(
        self,
        provider: IntegrationProvider,
        tenant_id: int,
        store_id: Optional[int],
        token_data: Dict[str, Any],
        shop_domain: Optional[str] = None,
    ):
        """Save or update integration connection"""
        from app.db.integration_models import IntegrationConfig
        
        # Check for existing connection
        existing = self.db.query(IntegrationConfig).filter(
            IntegrationConfig.provider == provider,
            # Would need tenant_id on IntegrationConfig
        ).first()
        
        if existing:
            # Update existing
            existing.api_key = token_data.get("access_token")
            existing.api_secret = token_data.get("refresh_token")
            # existing.token_expires_at = calculate expiry
            existing.is_active = True
            self.db.commit()
            return existing
        
        # Create new
        connection = IntegrationConfig(
            provider=provider,
            name=f"{provider.value} Integration",
            api_key=token_data.get("access_token", ""),
            api_secret=token_data.get("refresh_token"),
            sync_direction=SyncDirection.BIDIRECTIONAL,
            is_active=True,
        )
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        
        return connection
    
    async def refresh_token(
        self,
        connection_id: int,
    ) -> bool:
        """Refresh OAuth token"""
        from app.db.integration_models import IntegrationConfig
        
        connection = self.db.query(IntegrationConfig).filter(
            IntegrationConfig.id == connection_id
        ).first()
        
        if not connection or not connection.api_secret:
            return False
        
        config = OAUTH_CONFIGS.get(connection.provider)
        if not config:
            return False
        
        client_id = os.getenv(config["env_client_id"])
        client_secret = os.getenv(config["env_client_secret"])
        
        if not client_id or not client_secret:
            return False
        
        async with httpx.AsyncClient() as client:
            if connection.provider == IntegrationProvider.QUICKBOOKS:
                auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                response = await client.post(
                    config["token_url"],
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": connection.api_secret,
                    },
                )
            else:
                response = await client.post(
                    config["token_url"],
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": connection.api_secret,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                )
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            connection.is_active = False
            self.db.commit()
            return False
        
        token_data = response.json()
        connection.api_key = token_data.get("access_token")
        if "refresh_token" in token_data:
            connection.api_secret = token_data["refresh_token"]
        
        self.db.commit()
        return True


class QuickBooksService:
    """QuickBooks API integration"""
    
    def __init__(self, db: Session, connection_id: int):
        self.db = db
        self.connection_id = connection_id
        self._connection = None
    
    @property
    def connection(self):
        if not self._connection:
            from app.db.integration_models import IntegrationConfig
            self._connection = self.db.query(IntegrationConfig).filter(
                IntegrationConfig.id == self.connection_id
            ).first()
        return self._connection
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        realm_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make authenticated API request"""
        if not self.connection:
            raise ValueError("Connection not found")
        
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.connection.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        
        if response.status_code == 401:
            # Token expired, try refresh
            oauth = OAuthService(self.db)
            if await oauth.refresh_token(self.connection_id):
                # Retry request
                self._connection = None  # Clear cache
                return await self._request(method, endpoint, realm_id, **kwargs)
            raise ValueError("Authentication failed")
        
        response.raise_for_status()
        return response.json()
    
    async def get_company_info(self, realm_id: str) -> Dict[str, Any]:
        """Get company information"""
        return await self._request("GET", "companyinfo/" + realm_id, realm_id)
    
    async def sync_sales(self, realm_id: str, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync sale as invoice/sales receipt"""
        return await self._request(
            "POST",
            "salesreceipt",
            realm_id,
            json=sales_data,
        )
    
    async def get_items(self, realm_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get inventory items"""
        query = f"SELECT * FROM Item MAXRESULTS {limit}"
        return await self._request(
            "GET",
            f"query?query={query}",
            realm_id,
        )


class ShopifyService:
    """Shopify API integration"""
    
    def __init__(self, db: Session, connection_id: int, shop_domain: str):
        self.db = db
        self.connection_id = connection_id
        self.shop_domain = shop_domain
        self._connection = None
    
    @property
    def connection(self):
        if not self._connection:
            from app.db.integration_models import IntegrationConfig
            self._connection = self.db.query(IntegrationConfig).filter(
                IntegrationConfig.id == self.connection_id
            ).first()
        return self._connection
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make authenticated API request"""
        if not self.connection:
            raise ValueError("Connection not found")
        
        url = f"https://{self.shop_domain}.myshopify.com/admin/api/2024-01/{endpoint}"
        
        headers = {
            "X-Shopify-Access-Token": self.connection.api_key,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        
        response.raise_for_status()
        return response.json()
    
    async def get_products(self, limit: int = 50) -> Dict[str, Any]:
        """Get products from Shopify"""
        return await self._request("GET", f"products.json?limit={limit}")
    
    async def update_inventory(self, inventory_item_id: int, available: int, location_id: int) -> Dict[str, Any]:
        """Update inventory level"""
        return await self._request(
            "POST",
            "inventory_levels/set.json",
            json={
                "inventory_item_id": inventory_item_id,
                "available": available,
                "location_id": location_id,
            },
        )
    
    async def get_orders(self, status: str = "any", limit: int = 50) -> Dict[str, Any]:
        """Get orders from Shopify"""
        return await self._request("GET", f"orders.json?status={status}&limit={limit}")
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """Verify Shopify webhook signature"""
        client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
        if not client_secret:
            return False
        
        computed_hmac = base64.b64encode(
            hmac.new(
                client_secret.encode(),
                data,
                hashlib.sha256,
            ).digest()
        ).decode()
        
        return hmac.compare_digest(computed_hmac, hmac_header)


class SquareService:
    """Square API integration"""
    
    def __init__(self, db: Session, connection_id: int):
        self.db = db
        self.connection_id = connection_id
        self._connection = None
    
    @property
    def connection(self):
        if not self._connection:
            from app.db.integration_models import IntegrationConfig
            self._connection = self.db.query(IntegrationConfig).filter(
                IntegrationConfig.id == self.connection_id
            ).first()
        return self._connection
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make authenticated API request"""
        if not self.connection:
            raise ValueError("Connection not found")
        
        url = f"https://connect.squareup.com/v2/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.connection.api_key}",
            "Content-Type": "application/json",
            "Square-Version": "2024-01-18",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        
        if response.status_code == 401:
            oauth = OAuthService(self.db)
            if await oauth.refresh_token(self.connection_id):
                self._connection = None
                return await self._request(method, endpoint, **kwargs)
            raise ValueError("Authentication failed")
        
        response.raise_for_status()
        return response.json()
    
    async def get_locations(self) -> Dict[str, Any]:
        """Get Square locations"""
        return await self._request("GET", "locations")
    
    async def get_catalog(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get catalog items"""
        endpoint = "catalog/list?types=ITEM"
        if cursor:
            endpoint += f"&cursor={cursor}"
        return await self._request("GET", endpoint)
    
    async def get_inventory(self, location_id: str) -> Dict[str, Any]:
        """Get inventory counts"""
        return await self._request(
            "POST",
            "inventory/counts/batch-retrieve",
            json={"location_ids": [location_id]},
        )
