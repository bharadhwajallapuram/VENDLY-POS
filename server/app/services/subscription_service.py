"""
Vendly POS - Subscription Service
==================================
Stripe subscription management and billing
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.subscription_models import (
    BillingInterval,
    Invoice,
    InvoiceStatus,
    Plan,
    PlanTier,
    Store,
    Subscription,
    SubscriptionStatus,
    Tenant,
    TenantUser,
    UsageEvent,
)

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# ============================================
# Plan Management
# ============================================

DEFAULT_PLANS = [
    {
        "name": "Free",
        "tier": PlanTier.FREE.value,
        "description": "Perfect for trying out Vendly",
        "price_monthly": 0,
        "price_yearly": 0,
        "max_stores": 1,
        "max_users": 1,
        "max_products": 50,
        "max_transactions_monthly": 100,
        "feature_inventory": True,
        "feature_reports": True,
        "feature_advanced_reports": False,
        "feature_api_access": False,
        "feature_custom_branding": False,
        "feature_priority_support": False,
        "feature_ai_insights": False,
        "feature_multi_store": False,
        "feature_integrations": False,
        "sort_order": 1,
    },
    {
        "name": "Starter",
        "tier": PlanTier.STARTER.value,
        "description": "For small businesses getting started",
        "price_monthly": 29,
        "price_yearly": 290,  # ~2 months free
        "max_stores": 1,
        "max_users": 3,
        "max_products": 500,
        "max_transactions_monthly": 1000,
        "feature_inventory": True,
        "feature_reports": True,
        "feature_advanced_reports": True,
        "feature_api_access": False,
        "feature_custom_branding": False,
        "feature_priority_support": False,
        "feature_ai_insights": False,
        "feature_multi_store": False,
        "feature_integrations": True,
        "sort_order": 2,
    },
    {
        "name": "Professional",
        "tier": PlanTier.PROFESSIONAL.value,
        "description": "For growing businesses with multiple locations",
        "price_monthly": 79,
        "price_yearly": 790,
        "max_stores": 5,
        "max_users": 15,
        "max_products": 5000,
        "max_transactions_monthly": 10000,
        "feature_inventory": True,
        "feature_reports": True,
        "feature_advanced_reports": True,
        "feature_api_access": True,
        "feature_custom_branding": True,
        "feature_priority_support": True,
        "feature_ai_insights": True,
        "feature_multi_store": True,
        "feature_integrations": True,
        "sort_order": 3,
    },
    {
        "name": "Enterprise",
        "tier": PlanTier.ENTERPRISE.value,
        "description": "For large organizations with custom needs",
        "price_monthly": 199,
        "price_yearly": 1990,
        "max_stores": 999,  # Unlimited
        "max_users": 999,
        "max_products": 999999,
        "max_transactions_monthly": 999999,
        "feature_inventory": True,
        "feature_reports": True,
        "feature_advanced_reports": True,
        "feature_api_access": True,
        "feature_custom_branding": True,
        "feature_priority_support": True,
        "feature_ai_insights": True,
        "feature_multi_store": True,
        "feature_integrations": True,
        "sort_order": 4,
    },
]


def seed_plans(db: Session) -> List[Plan]:
    """Seed default subscription plans"""
    plans = []
    for plan_data in DEFAULT_PLANS:
        existing = db.query(Plan).filter(Plan.tier == plan_data["tier"]).first()
        if not existing:
            plan = Plan(**plan_data)
            db.add(plan)
            plans.append(plan)
            logger.info(f"Created plan: {plan_data['name']}")
        else:
            plans.append(existing)
    db.commit()
    return plans


def sync_plans_to_stripe(db: Session) -> None:
    """Sync plans to Stripe as Products/Prices"""
    if not settings.STRIPE_SECRET_KEY:
        logger.warning("Stripe not configured, skipping plan sync")
        return

    plans = db.query(Plan).filter(Plan.is_active == True).all()
    
    for plan in plans:
        try:
            # Create or update Stripe Product
            if plan.stripe_product_id:
                product = stripe.Product.modify(
                    plan.stripe_product_id,
                    name=f"Vendly {plan.name}",
                    description=plan.description,
                )
            else:
                product = stripe.Product.create(
                    name=f"Vendly {plan.name}",
                    description=plan.description,
                    metadata={"plan_id": str(plan.id), "tier": plan.tier},
                )
                plan.stripe_product_id = product.id

            # Create monthly price if needed
            if plan.price_monthly > 0 and not plan.stripe_price_monthly_id:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan.price_monthly * 100),  # cents
                    currency=plan.currency.lower(),
                    recurring={"interval": "month"},
                    metadata={"plan_id": str(plan.id), "interval": "monthly"},
                )
                plan.stripe_price_monthly_id = price.id

            # Create yearly price if needed
            if plan.price_yearly > 0 and not plan.stripe_price_yearly_id:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan.price_yearly * 100),
                    currency=plan.currency.lower(),
                    recurring={"interval": "year"},
                    metadata={"plan_id": str(plan.id), "interval": "yearly"},
                )
                plan.stripe_price_yearly_id = price.id

            db.commit()
            logger.info(f"Synced plan to Stripe: {plan.name}")
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error syncing plan {plan.name}: {e}")


# ============================================
# Tenant Management
# ============================================

def create_tenant(
    db: Session,
    name: str,
    email: str,
    slug: str,
    user_id: int,
    **kwargs
) -> Tenant:
    """Create a new tenant with owner"""
    # Create tenant
    tenant = Tenant(
        name=name,
        email=email,
        slug=slug,
        **kwargs
    )
    db.add(tenant)
    db.flush()

    # Create Stripe customer
    if settings.STRIPE_SECRET_KEY:
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"tenant_id": str(tenant.id)},
            )
            tenant.stripe_customer_id = customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")

    # Add owner as tenant user
    tenant_user = TenantUser(
        tenant_id=tenant.id,
        user_id=user_id,
        role="owner",
        accepted_at=datetime.utcnow(),
    )
    db.add(tenant_user)

    # Create default store
    store = Store(
        tenant_id=tenant.id,
        name=f"{name} - Main Store",
        code="MAIN",
    )
    db.add(store)

    # Create free subscription
    free_plan = db.query(Plan).filter(Plan.tier == PlanTier.FREE.value).first()
    if free_plan:
        subscription = Subscription(
            tenant_id=tenant.id,
            plan_id=free_plan.id,
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=36500),  # "Forever"
        )
        db.add(subscription)

    db.commit()
    db.refresh(tenant)
    return tenant


def get_tenant_subscription(db: Session, tenant_id: int) -> Optional[Subscription]:
    """Get active subscription for tenant"""
    return db.query(Subscription).filter(
        Subscription.tenant_id == tenant_id,
        Subscription.status.in_([
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ])
    ).first()


def get_tenant_limits(db: Session, tenant_id: int) -> Dict[str, Any]:
    """Get current limits for tenant based on subscription"""
    subscription = get_tenant_subscription(db, tenant_id)
    
    if not subscription:
        # Return free tier limits
        return {
            "max_stores": 1,
            "max_users": 1,
            "max_products": 50,
            "max_transactions_monthly": 100,
            "features": {
                "inventory": True,
                "reports": True,
                "advanced_reports": False,
                "api_access": False,
                "custom_branding": False,
                "priority_support": False,
                "ai_insights": False,
                "multi_store": False,
                "integrations": False,
            }
        }
    
    plan = subscription.plan
    return {
        "max_stores": plan.max_stores,
        "max_users": plan.max_users,
        "max_products": plan.max_products,
        "max_transactions_monthly": plan.max_transactions_monthly,
        "transactions_used": subscription.transactions_this_month,
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
        }
    }


# ============================================
# Subscription Management
# ============================================

def create_checkout_session(
    db: Session,
    tenant_id: int,
    plan_id: int,
    billing_interval: str = "monthly",
    success_url: str = "",
    cancel_url: str = "",
) -> Dict[str, Any]:
    """Create Stripe Checkout session for subscription"""
    tenant = db.get(Tenant, tenant_id)
    plan = db.get(Plan, plan_id)
    
    if not tenant or not plan:
        raise ValueError("Tenant or Plan not found")

    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("Stripe not configured")

    price_id = (
        plan.stripe_price_monthly_id 
        if billing_interval == "monthly" 
        else plan.stripe_price_yearly_id
    )
    
    if not price_id:
        raise ValueError(f"No Stripe price configured for {plan.name} ({billing_interval})")

    try:
        # Create or get Stripe customer
        if not tenant.stripe_customer_id:
            customer = stripe.Customer.create(
                email=tenant.email,
                name=tenant.name,
                metadata={"tenant_id": str(tenant.id)},
            )
            tenant.stripe_customer_id = customer.id
            db.commit()

        session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url or f"{settings.CORS_ORIGINS[0]}/settings/billing?success=true",
            cancel_url=cancel_url or f"{settings.CORS_ORIGINS[0]}/settings/billing?canceled=true",
            metadata={
                "tenant_id": str(tenant_id),
                "plan_id": str(plan_id),
                "billing_interval": billing_interval,
            },
            subscription_data={
                "metadata": {
                    "tenant_id": str(tenant_id),
                    "plan_id": str(plan_id),
                },
                "trial_period_days": 14 if plan.tier != PlanTier.FREE.value else None,
            },
        )
        
        return {
            "session_id": session.id,
            "url": session.url,
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise ValueError(str(e))


def create_billing_portal_session(
    db: Session,
    tenant_id: int,
    return_url: str = "",
) -> Dict[str, str]:
    """Create Stripe Customer Portal session"""
    tenant = db.get(Tenant, tenant_id)
    
    if not tenant or not tenant.stripe_customer_id:
        raise ValueError("Tenant not found or no Stripe customer")

    try:
        session = stripe.billing_portal.Session.create(
            customer=tenant.stripe_customer_id,
            return_url=return_url or f"{settings.CORS_ORIGINS[0]}/settings/billing",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise ValueError(str(e))


def cancel_subscription(
    db: Session,
    tenant_id: int,
    at_period_end: bool = True,
) -> Subscription:
    """Cancel subscription"""
    subscription = get_tenant_subscription(db, tenant_id)
    
    if not subscription:
        raise ValueError("No active subscription found")

    if subscription.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
                subscription.cancel_at_period_end = True
            else:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED.value
                subscription.canceled_at = datetime.utcnow()
        except stripe.error.StripeError as e:
            logger.error(f"Stripe cancel error: {e}")
            raise ValueError(str(e))
    else:
        subscription.status = SubscriptionStatus.CANCELED.value
        subscription.canceled_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)
    return subscription


# ============================================
# Webhook Handlers
# ============================================

def handle_subscription_created(db: Session, event_data: Dict[str, Any]) -> None:
    """Handle subscription.created webhook"""
    stripe_sub = event_data["object"]
    tenant_id = stripe_sub.get("metadata", {}).get("tenant_id")
    plan_id = stripe_sub.get("metadata", {}).get("plan_id")
    
    if not tenant_id:
        logger.warning("No tenant_id in subscription metadata")
        return

    tenant = db.get(Tenant, int(tenant_id))
    if not tenant:
        logger.warning(f"Tenant {tenant_id} not found")
        return

    # Find or create subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub["id"]
    ).first()
    
    if not subscription:
        subscription = Subscription(
            tenant_id=int(tenant_id),
            plan_id=int(plan_id) if plan_id else 1,
            stripe_subscription_id=stripe_sub["id"],
        )
        db.add(subscription)

    subscription.status = stripe_sub["status"]
    subscription.stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
    subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
    
    if stripe_sub.get("trial_start"):
        subscription.trial_start = datetime.fromtimestamp(stripe_sub["trial_start"])
    if stripe_sub.get("trial_end"):
        subscription.trial_end = datetime.fromtimestamp(stripe_sub["trial_end"])

    db.commit()
    logger.info(f"Subscription created for tenant {tenant_id}")


def handle_subscription_updated(db: Session, event_data: Dict[str, Any]) -> None:
    """Handle subscription.updated webhook"""
    stripe_sub = event_data["object"]
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub["id"]
    ).first()
    
    if not subscription:
        logger.warning(f"Subscription {stripe_sub['id']} not found")
        return

    subscription.status = stripe_sub["status"]
    subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
    subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
    subscription.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
    
    if stripe_sub.get("canceled_at"):
        subscription.canceled_at = datetime.fromtimestamp(stripe_sub["canceled_at"])

    db.commit()
    logger.info(f"Subscription updated: {stripe_sub['id']}")


def handle_subscription_deleted(db: Session, event_data: Dict[str, Any]) -> None:
    """Handle subscription.deleted webhook"""
    stripe_sub = event_data["object"]
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub["id"]
    ).first()
    
    if subscription:
        subscription.status = SubscriptionStatus.CANCELED.value
        subscription.canceled_at = datetime.utcnow()
        db.commit()
        
        # Downgrade to free plan
        tenant = db.get(Tenant, subscription.tenant_id)
        if tenant:
            free_plan = db.query(Plan).filter(Plan.tier == PlanTier.FREE.value).first()
            if free_plan:
                new_sub = Subscription(
                    tenant_id=tenant.id,
                    plan_id=free_plan.id,
                    status=SubscriptionStatus.ACTIVE.value,
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=36500),
                )
                db.add(new_sub)
                db.commit()
        
        logger.info(f"Subscription canceled: {stripe_sub['id']}")


def handle_invoice_paid(db: Session, event_data: Dict[str, Any]) -> None:
    """Handle invoice.paid webhook"""
    stripe_invoice = event_data["object"]
    customer_id = stripe_invoice.get("customer")
    
    tenant = db.query(Tenant).filter(Tenant.stripe_customer_id == customer_id).first()
    if not tenant:
        logger.warning(f"Tenant not found for customer {customer_id}")
        return

    # Create or update invoice record
    invoice = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == stripe_invoice["id"]
    ).first()
    
    if not invoice:
        invoice = Invoice(
            tenant_id=tenant.id,
            stripe_invoice_id=stripe_invoice["id"],
            invoice_number=stripe_invoice.get("number", f"INV-{stripe_invoice['id'][-8:]}"),
        )
        db.add(invoice)

    invoice.status = InvoiceStatus.PAID.value
    invoice.subtotal = stripe_invoice["subtotal"] / 100
    invoice.tax = stripe_invoice.get("tax", 0) / 100
    invoice.total = stripe_invoice["total"] / 100
    invoice.amount_paid = stripe_invoice["amount_paid"] / 100
    invoice.amount_due = stripe_invoice["amount_due"] / 100
    invoice.paid_at = datetime.utcnow()
    invoice.invoice_pdf_url = stripe_invoice.get("invoice_pdf")
    invoice.hosted_invoice_url = stripe_invoice.get("hosted_invoice_url")

    db.commit()
    logger.info(f"Invoice paid: {stripe_invoice['id']}")


def handle_invoice_payment_failed(db: Session, event_data: Dict[str, Any]) -> None:
    """Handle invoice.payment_failed webhook"""
    stripe_invoice = event_data["object"]
    customer_id = stripe_invoice.get("customer")
    
    tenant = db.query(Tenant).filter(Tenant.stripe_customer_id == customer_id).first()
    if tenant:
        # Update subscription status
        subscription = get_tenant_subscription(db, tenant.id)
        if subscription:
            subscription.status = SubscriptionStatus.PAST_DUE.value
            db.commit()
        
        # TODO: Send notification email
        logger.warning(f"Payment failed for tenant {tenant.id}")


# ============================================
# Usage Tracking
# ============================================

def record_usage(
    db: Session,
    tenant_id: int,
    event_type: str,
    quantity: int = 1,
    store_id: Optional[int] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Record usage event for metered billing"""
    event = UsageEvent(
        tenant_id=tenant_id,
        store_id=store_id,
        event_type=event_type,
        quantity=quantity,
        event_metadata=str(metadata) if metadata else None,
    )
    db.add(event)
    
    # Update subscription counter
    if event_type == "transaction":
        subscription = get_tenant_subscription(db, tenant_id)
        if subscription:
            subscription.transactions_this_month += quantity
    
    db.commit()


def check_usage_limit(
    db: Session,
    tenant_id: int,
    limit_type: str,
) -> Dict[str, Any]:
    """Check if tenant is within usage limits"""
    limits = get_tenant_limits(db, tenant_id)
    subscription = get_tenant_subscription(db, tenant_id)
    
    if limit_type == "transactions":
        used = subscription.transactions_this_month if subscription else 0
        max_allowed = limits["max_transactions_monthly"]
        return {
            "allowed": used < max_allowed,
            "used": used,
            "max": max_allowed,
            "remaining": max(0, max_allowed - used),
        }
    
    if limit_type == "stores":
        used = db.query(Store).filter(Store.tenant_id == tenant_id, Store.is_active == True).count()
        max_allowed = limits["max_stores"]
        return {
            "allowed": used < max_allowed,
            "used": used,
            "max": max_allowed,
            "remaining": max(0, max_allowed - used),
        }
    
    if limit_type == "users":
        used = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.is_active == True
        ).count()
        max_allowed = limits["max_users"]
        return {
            "allowed": used < max_allowed,
            "used": used,
            "max": max_allowed,
            "remaining": max(0, max_allowed - used),
        }
    
    return {"allowed": True, "used": 0, "max": 999999, "remaining": 999999}


def reset_monthly_usage(db: Session) -> None:
    """Reset monthly usage counters (run via cron)"""
    subscriptions = db.query(Subscription).filter(
        Subscription.status.in_([
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ])
    ).all()
    
    for sub in subscriptions:
        sub.transactions_this_month = 0
        sub.usage_reset_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"Reset usage for {len(subscriptions)} subscriptions")
