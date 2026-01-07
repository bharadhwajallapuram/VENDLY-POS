"""
Vendly POS - Subscription & Billing API
========================================
Endpoints for subscription management, billing, and tenant operations
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.subscription_models import (
    BillingInterval,
    Invoice,
    Plan,
    Store,
    Subscription,
    Tenant,
    TenantUser,
)
from app.services.subscription_service import (
    cancel_subscription,
    check_usage_limit,
    create_billing_portal_session,
    create_checkout_session,
    create_tenant,
    get_tenant_limits,
    get_tenant_subscription,
    handle_invoice_paid,
    handle_invoice_payment_failed,
    handle_subscription_created,
    handle_subscription_deleted,
    handle_subscription_updated,
)
from app.api.v1.routers.payments import verify_stripe_signature

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_settings():
    from app.core.config import settings

    return settings


# ============================================
# Schemas
# ============================================


class PlanResponse(BaseModel):
    id: int
    name: str
    tier: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    currency: str
    max_stores: int
    max_users: int
    max_products: int
    max_transactions_monthly: int
    features: dict

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    name: str
    email: EmailStr
    slug: str
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    phone: Optional[str] = None
    country: str = "US"


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    email: str
    business_name: Optional[str]
    is_active: bool
    is_verified: bool
    currency: str
    country: str

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    stores: List[dict]
    subscription: Optional[dict]
    limits: dict


class StoreCreate(BaseModel):
    name: str
    code: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"


class StoreResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    code: str
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    plan_id: int
    plan_name: str
    status: str
    billing_interval: str
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    transactions_used: int
    transactions_limit: int

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    plan_id: int
    billing_interval: str = "monthly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class UsageLimitResponse(BaseModel):
    allowed: bool
    used: int
    max: int
    remaining: int


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    status: str
    total: float
    currency: str
    invoice_date: str
    paid_at: Optional[str]
    invoice_pdf_url: Optional[str]

    class Config:
        from_attributes = True


# ============================================
# Plans Endpoints
# ============================================


@router.get("/plans", response_model=List[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    include_private: bool = Query(False),
):
    """List all available subscription plans"""
    query = db.query(Plan).filter(Plan.is_active == True)

    if not include_private:
        query = query.filter(Plan.is_public == True)

    plans = query.order_by(Plan.sort_order).all()

    result = []
    for plan in plans:
        result.append(
            {
                "id": plan.id,
                "name": plan.name,
                "tier": plan.tier,
                "description": plan.description,
                "price_monthly": float(plan.price_monthly),
                "price_yearly": float(plan.price_yearly),
                "currency": plan.currency,
                "max_stores": plan.max_stores,
                "max_users": plan.max_users,
                "max_products": plan.max_products,
                "max_transactions_monthly": plan.max_transactions_monthly,
                "features": {
                    "inventory": plan.feature_inventory,
                    "reports": plan.feature_reports,
                    "advanced_reports": plan.feature_advanced_reports,
                    "api_access": plan.feature_api_access,
                    "custom_branding": plan.feature_custom_branding,
                    "priority_support": plan.feature_priority_support,
                    "ai_insights": plan.feature_ai_insights,
                    "multi_store": plan.feature_multi_store,
                    "integrations": plan.feature_integrations,
                },
            }
        )

    return result


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific plan by ID"""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "id": plan.id,
        "name": plan.name,
        "tier": plan.tier,
        "description": plan.description,
        "price_monthly": float(plan.price_monthly),
        "price_yearly": float(plan.price_yearly),
        "currency": plan.currency,
        "max_stores": plan.max_stores,
        "max_users": plan.max_users,
        "max_products": plan.max_products,
        "max_transactions_monthly": plan.max_transactions_monthly,
        "features": {
            "inventory": plan.feature_inventory,
            "reports": plan.feature_reports,
            "advanced_reports": plan.feature_advanced_reports,
            "api_access": plan.feature_api_access,
            "custom_branding": plan.feature_custom_branding,
            "priority_support": plan.feature_priority_support,
            "ai_insights": plan.feature_ai_insights,
            "multi_store": plan.feature_multi_store,
            "integrations": plan.feature_integrations,
        },
    }


# ============================================
# Tenant Endpoints
# ============================================


@router.post("/tenants", response_model=TenantResponse)
def create_new_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new tenant/organization"""
    # Check if slug is available
    existing = db.query(Tenant).filter(Tenant.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already taken")

    tenant = create_tenant(
        db=db,
        name=data.name,
        email=data.email,
        slug=data.slug,
        user_id=user.id,
        business_name=data.business_name,
        business_type=data.business_type,
        phone=data.phone,
        country=data.country,
    )

    return tenant


@router.get("/tenants/me", response_model=TenantDetailResponse)
def get_my_tenant(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get current user's tenant with subscription details"""
    # Find tenant user belongs to
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    tenant = db.get(Tenant, tenant_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get stores
    stores = (
        db.query(Store)
        .filter(Store.tenant_id == tenant.id, Store.is_active == True)
        .all()
    )

    # Get subscription
    subscription = get_tenant_subscription(db, tenant.id)
    sub_data = None
    if subscription:
        sub_data = {
            "id": subscription.id,
            "plan_name": subscription.plan.name,
            "plan_tier": subscription.plan.tier,
            "status": subscription.status,
            "billing_interval": subscription.billing_interval,
            "current_period_end": (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end
                else None
            ),
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    # Get limits
    limits = get_tenant_limits(db, tenant.id)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "business_name": tenant.business_name,
        "is_active": tenant.is_active,
        "is_verified": tenant.is_verified,
        "currency": tenant.currency,
        "country": tenant.country,
        "stores": [
            {"id": s.id, "name": s.name, "code": s.code, "city": s.city} for s in stores
        ],
        "subscription": sub_data,
        "limits": limits,
    }


@router.get("/tenants/{tenant_id}", response_model=TenantDetailResponse)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get tenant by ID (requires membership)"""
    # Verify user has access
    tenant_user = (
        db.query(TenantUser)
        .filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user.id,
            TenantUser.is_active == True,
        )
        .first()
    )

    if not tenant_user and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    stores = db.query(Store).filter(Store.tenant_id == tenant.id).all()
    subscription = get_tenant_subscription(db, tenant.id)
    limits = get_tenant_limits(db, tenant.id)

    sub_data = None
    if subscription:
        sub_data = {
            "id": subscription.id,
            "plan_name": subscription.plan.name,
            "plan_tier": subscription.plan.tier,
            "status": subscription.status,
            "billing_interval": subscription.billing_interval,
            "current_period_end": (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end
                else None
            ),
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "business_name": tenant.business_name,
        "is_active": tenant.is_active,
        "is_verified": tenant.is_verified,
        "currency": tenant.currency,
        "country": tenant.country,
        "stores": [
            {"id": s.id, "name": s.name, "code": s.code, "city": s.city} for s in stores
        ],
        "subscription": sub_data,
        "limits": limits,
    }


# ============================================
# Store Endpoints
# ============================================


@router.post("/tenants/{tenant_id}/stores", response_model=StoreResponse)
def create_store(
    tenant_id: int,
    data: StoreCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new store for tenant"""
    # Verify access
    tenant_user = (
        db.query(TenantUser)
        .filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user.id,
            TenantUser.role.in_(["owner", "admin"]),
            TenantUser.is_active == True,
        )
        .first()
    )

    if not tenant_user and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check limit
    limit_check = check_usage_limit(db, tenant_id, "stores")
    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=402,
            detail=f"Store limit reached ({limit_check['max']}). Please upgrade your plan.",
        )

    # Check for duplicate code
    existing = (
        db.query(Store)
        .filter(Store.tenant_id == tenant_id, Store.code == data.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Store code already exists")

    store = Store(
        tenant_id=tenant_id,
        name=data.name,
        code=data.code,
        email=data.email,
        phone=data.phone,
        address_line1=data.address_line1,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        country=data.country,
    )
    db.add(store)
    db.commit()
    db.refresh(store)

    return store


@router.get("/tenants/{tenant_id}/stores", response_model=List[StoreResponse])
def list_stores(
    tenant_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all stores for a tenant"""
    tenant_user = (
        db.query(TenantUser)
        .filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user.id,
            TenantUser.is_active == True,
        )
        .first()
    )

    if not tenant_user and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    stores = db.query(Store).filter(Store.tenant_id == tenant_id).all()
    return stores


# ============================================
# Subscription Endpoints
# ============================================


@router.get("/subscription", response_model=SubscriptionResponse)
def get_my_subscription(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get current user's subscription"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found")

    subscription = get_tenant_subscription(db, tenant_user.tenant_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")

    return {
        "id": subscription.id,
        "tenant_id": subscription.tenant_id,
        "plan_id": subscription.plan_id,
        "plan_name": subscription.plan.name,
        "status": subscription.status,
        "billing_interval": subscription.billing_interval,
        "current_period_start": (
            subscription.current_period_start.isoformat()
            if subscription.current_period_start
            else None
        ),
        "current_period_end": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "transactions_used": subscription.transactions_this_month,
        "transactions_limit": subscription.plan.max_transactions_monthly,
    }


@router.post("/subscription/checkout")
def create_subscription_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create Stripe checkout session for subscription upgrade"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found")

    try:
        result = create_checkout_session(
            db=db,
            tenant_id=tenant_user.tenant_id,
            plan_id=data.plan_id,
            billing_interval=data.billing_interval,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription/portal")
def create_portal_session(
    return_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create Stripe billing portal session"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found")

    try:
        result = create_billing_portal_session(
            db=db,
            tenant_id=tenant_user.tenant_id,
            return_url=return_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription/cancel")
def cancel_my_subscription(
    at_period_end: bool = Query(True),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Cancel subscription"""
    tenant_user = (
        db.query(TenantUser)
        .filter(
            TenantUser.user_id == user.id,
            TenantUser.role.in_(["owner", "admin"]),
            TenantUser.is_active == True,
        )
        .first()
    )

    if not tenant_user:
        raise HTTPException(
            status_code=403, detail="Only owners can cancel subscriptions"
        )

    try:
        subscription = cancel_subscription(
            db=db,
            tenant_id=tenant_user.tenant_id,
            at_period_end=at_period_end,
        )
        return {
            "message": "Subscription will be canceled"
            + (" at period end" if at_period_end else ""),
            "status": subscription.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Usage & Limits Endpoints
# ============================================


@router.get("/usage/{limit_type}", response_model=UsageLimitResponse)
def check_limit(
    limit_type: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Check usage against limit (transactions, stores, users)"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found")

    result = check_usage_limit(db, tenant_user.tenant_id, limit_type)
    return result


# ============================================
# Invoices Endpoints
# ============================================


@router.get("/invoices", response_model=List[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = Query(20, le=100),
):
    """List invoices for current tenant"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user.id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        raise HTTPException(status_code=404, detail="No tenant found")

    invoices = (
        db.query(Invoice)
        .filter(Invoice.tenant_id == tenant_user.tenant_id)
        .order_by(Invoice.invoice_date.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "total": float(inv.total),
            "currency": inv.currency,
            "invoice_date": inv.invoice_date.isoformat(),
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            "invoice_pdf_url": inv.invoice_pdf_url,
        }
        for inv in invoices
    ]


# ============================================
# Stripe Webhook
# ============================================


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhooks for subscription events"""
    settings = _get_settings()

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()

    try:
        event = verify_stripe_signature(
            payload=payload,
            signature=stripe_signature,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        logger.warning(f"Invalid Stripe signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    event_data = event.get("data", {})

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "customer.subscription.created":
            handle_subscription_created(db, event_data)
        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(db, event_data)
        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(db, event_data)
        elif event_type == "invoice.paid":
            handle_invoice_paid(db, event_data)
        elif event_type == "invoice.payment_failed":
            handle_invoice_payment_failed(db, event_data)
        else:
            logger.debug(f"Unhandled webhook event: {event_type}")
    except Exception as e:
        logger.error(f"Error handling webhook {event_type}: {e}", exc_info=True)
        # Don't raise - Stripe will retry

    return {"received": True}
