"""
Vendly POS - OAuth Integration Router
======================================
OAuth callbacks and integration management
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.integration_models import IntegrationConfig, IntegrationProvider
from app.db.subscription_models import TenantUser
from app.services.oauth_service import OAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])


# ============================================
# Schemas
# ============================================


class ConnectRequest(BaseModel):
    provider: str
    shop_domain: Optional[str] = None  # For Shopify
    store_id: Optional[int] = None


class ConnectionResponse(BaseModel):
    id: int
    provider: str
    name: str
    is_active: bool
    last_sync: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class AuthUrlResponse(BaseModel):
    auth_url: str
    state: str


# ============================================
# Helper Functions
# ============================================


def get_user_tenant_id(db: Session, user_id: int) -> Optional[int]:
    """Get tenant ID for user"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user_id, TenantUser.is_active == True)
        .first()
    )
    return tenant_user.tenant_id if tenant_user else None


def get_base_url(request: Request) -> str:
    """Get base URL from request"""
    return str(request.base_url).rstrip("/")


# ============================================
# Connection Management
# ============================================


@router.get("/connections", response_model=list[ConnectionResponse])
def list_connections(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all integration connections for the tenant"""
    connections = (
        db.query(IntegrationConfig).filter(IntegrationConfig.is_active == True).all()
    )

    result = []
    for conn in connections:
        result.append(
            ConnectionResponse(
                id=conn.id,
                provider=(
                    conn.provider.value
                    if hasattr(conn.provider, "value")
                    else str(conn.provider)
                ),
                name=conn.name,
                is_active=conn.is_active,
                last_sync=(
                    str(conn.last_sync_at)
                    if hasattr(conn, "last_sync_at") and conn.last_sync_at
                    else None
                ),
                status="connected" if conn.is_active else "disconnected",
            )
        )

    return result


@router.post("/connect", response_model=AuthUrlResponse)
async def initiate_connection(
    request: Request,
    connect_data: ConnectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Initiate OAuth connection to a provider"""
    tenant_id = get_user_tenant_id(db, current_user.id)
    if not tenant_id:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Map string to enum
    try:
        provider = IntegrationProvider(connect_data.provider)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {connect_data.provider}"
        )

    base_url = get_base_url(request)
    redirect_uri = f"{base_url}/api/v1/oauth/callback/{connect_data.provider}"

    oauth_service = OAuthService(db)

    try:
        result = oauth_service.get_auth_url(
            provider=provider,
            redirect_uri=redirect_uri,
            tenant_id=tenant_id,
            store_id=connect_data.store_id,
            shop_domain=connect_data.shop_domain,
        )
        return AuthUrlResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    realmId: Optional[str] = Query(None),  # QuickBooks realm ID
    shop: Optional[str] = Query(None),  # Shopify shop domain
    db: Session = Depends(get_db),
):
    """OAuth callback handler"""
    try:
        provider_enum = IntegrationProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    base_url = get_base_url(request)
    redirect_uri = f"{base_url}/api/v1/oauth/callback/{provider}"

    oauth_service = OAuthService(db)

    try:
        result = await oauth_service.exchange_code(
            provider=provider_enum,
            code=code,
            redirect_uri=redirect_uri,
            state=state,
            shop_domain=shop,
        )

        # Redirect to frontend success page
        frontend_url = base_url.replace(":8000", ":3000")  # Adjust for dev
        return RedirectResponse(
            url=f"{frontend_url}/settings/integrations?connected={provider}&status=success",
            status_code=302,
        )
    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        frontend_url = base_url.replace(":8000", ":3000")
        return RedirectResponse(
            url=f"{frontend_url}/settings/integrations?connected={provider}&status=error&message={str(e)}",
            status_code=302,
        )


@router.delete("/connections/{connection_id}")
async def disconnect(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Disconnect an integration"""
    connection = (
        db.query(IntegrationConfig)
        .filter(IntegrationConfig.id == connection_id)
        .first()
    )

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.is_active = False
    connection.api_key = None
    connection.api_secret = None
    db.commit()

    return {"message": "Disconnected successfully"}


# ============================================
# Sync Endpoints
# ============================================


@router.post("/connections/{connection_id}/sync")
async def trigger_sync(
    connection_id: int,
    sync_type: str = Query(
        "all", pattern="^(all|products|orders|inventory|customers)$"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger a sync operation"""
    connection = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.id == connection_id, IntegrationConfig.is_active == True
        )
        .first()
    )

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found or inactive")

    # TODO: Implement actual sync logic based on provider
    # This would queue a background job

    return {
        "message": "Sync initiated",
        "connection_id": connection_id,
        "sync_type": sync_type,
        "status": "queued",
    }


@router.get("/connections/{connection_id}/status")
async def get_connection_status(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed connection status"""
    connection = (
        db.query(IntegrationConfig)
        .filter(IntegrationConfig.id == connection_id)
        .first()
    )

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {
        "id": connection.id,
        "provider": (
            connection.provider.value
            if hasattr(connection.provider, "value")
            else str(connection.provider)
        ),
        "name": connection.name,
        "is_active": connection.is_active,
        "sync_direction": (
            connection.sync_direction.value
            if hasattr(connection.sync_direction, "value")
            else str(connection.sync_direction)
        ),
        "last_sync_at": (
            str(connection.last_sync_at)
            if hasattr(connection, "last_sync_at") and connection.last_sync_at
            else None
        ),
        "sync_frequency": connection.sync_frequency,
        "has_access_token": bool(connection.api_key),
        "has_refresh_token": bool(connection.api_secret),
    }
