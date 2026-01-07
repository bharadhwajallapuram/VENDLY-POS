"""
Seed script for subscription demo data
Run with: python -m scripts.seed_subscriptions
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.subscription_models import (
    Plan, Tenant, Store, TenantUser, Subscription, 
    SubscriptionStatus, BillingInterval
)
from app.db.models import User


def seed_plans(db):
    """Seed default plans"""
    plans_data = [
        {
            "name": "Free",
            "tier": "free",
            "description": "Perfect for trying out Vendly",
            "price_monthly": 0,
            "price_yearly": 0,
            "max_stores": 1,
            "max_users": 1,
            "max_products": 50,
            "max_transactions_monthly": 100,
            "features": {
                "basic_pos": True,
                "basic_reports": True,
                "email_support": True,
            },
            "sort_order": 0,
        },
        {
            "name": "Starter",
            "tier": "starter",
            "description": "For small businesses getting started",
            "price_monthly": 29,
            "price_yearly": 290,
            "max_stores": 1,
            "max_users": 3,
            "max_products": 500,
            "max_transactions_monthly": 1000,
            "features": {
                "basic_pos": True,
                "basic_reports": True,
                "inventory_management": True,
                "customer_management": True,
                "email_support": True,
            },
            "sort_order": 1,
        },
        {
            "name": "Professional",
            "tier": "professional",
            "description": "For growing businesses",
            "price_monthly": 79,
            "price_yearly": 790,
            "max_stores": 3,
            "max_users": 10,
            "max_products": 5000,
            "max_transactions_monthly": 10000,
            "features": {
                "basic_pos": True,
                "advanced_reports": True,
                "inventory_management": True,
                "customer_management": True,
                "demand_forecasting": True,
                "multi_store": True,
                "api_access": True,
                "priority_support": True,
            },
            "sort_order": 2,
        },
        {
            "name": "Enterprise",
            "tier": "enterprise",
            "description": "For large organizations",
            "price_monthly": 199,
            "price_yearly": 1990,
            "max_stores": 999,
            "max_users": 999,
            "max_products": 999999,
            "max_transactions_monthly": 999999,
            "features": {
                "basic_pos": True,
                "advanced_reports": True,
                "inventory_management": True,
                "customer_management": True,
                "demand_forecasting": True,
                "multi_store": True,
                "api_access": True,
                "white_label": True,
                "dedicated_support": True,
                "custom_integrations": True,
                "sla_guarantee": True,
            },
            "sort_order": 3,
        },
    ]

    for plan_data in plans_data:
        existing = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
        if not existing:
            plan = Plan(**plan_data)
            db.add(plan)
            print(f"  ✓ Created plan: {plan_data['name']}")
        else:
            print(f"  - Plan exists: {plan_data['name']}")

    db.commit()


def seed_demo_tenant(db):
    """Create a demo tenant for the first user"""
    # Get the first user
    user = db.query(User).first()
    if not user:
        print("  ✗ No users found. Please create a user first.")
        return None

    # Check if user already has a tenant
    existing = db.query(TenantUser).filter(TenantUser.user_id == user.id).first()
    if existing:
        print(f"  - User already has tenant: {existing.tenant.name}")
        return existing.tenant

    # Get the Professional plan
    plan = db.query(Plan).filter(Plan.tier == "professional").first()
    if not plan:
        print("  ✗ No plans found. Run seed_plans first.")
        return None

    # Create tenant
    tenant = Tenant(
        name="Demo Business",
        slug="demo-business",
        email=user.email,
        business_name="Demo Retail Store",
        business_type="retail",
        phone="+1-555-0123",
        country="US",
        timezone="America/New_York",
        currency="USD",
    )
    db.add(tenant)
    db.flush()
    print(f"  ✓ Created tenant: {tenant.name}")

    # Create primary store
    store = Store(
        tenant_id=tenant.id,
        name="Main Store",
        code="MAIN-001",
        address_line1="123 Demo Street",
        city="New York",
        state="NY",
        postal_code="10001",
        country="US",
        timezone="America/New_York",
    )
    db.add(store)
    print(f"  ✓ Created store: {store.name}")

    # Link user to tenant as owner
    tenant_user = TenantUser(
        tenant_id=tenant.id,
        user_id=user.id,
        role="owner",
        accepted_at=datetime.utcnow(),
    )
    db.add(tenant_user)
    print(f"  ✓ Linked user {user.email} as owner")

    # Find or create manager user and link to tenant
    manager_user = db.query(User).filter(User.email == "manager@vendly.com").first()
    if manager_user:
        existing_manager = db.query(TenantUser).filter(
            TenantUser.user_id == manager_user.id,
            TenantUser.tenant_id == tenant.id
        ).first()
        if not existing_manager:
            manager_tenant_user = TenantUser(
                tenant_id=tenant.id,
                user_id=manager_user.id,
                role="manager",
                accepted_at=datetime.utcnow(),
            )
            db.add(manager_tenant_user)
            print(f"  ✓ Linked user {manager_user.email} as manager")
        else:
            print(f"  - Manager already linked: {manager_user.email}")
    else:
        print("  - No manager@vendly.com user found (skipping)")

    # Create subscription (14-day trial on Professional)
    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        status=SubscriptionStatus.TRIALING.value,
        billing_interval=BillingInterval.MONTHLY.value,
        trial_start=datetime.utcnow(),
        trial_end=datetime.utcnow() + timedelta(days=14),
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=14),
        transactions_this_month=42,  # Demo usage
    )
    db.add(subscription)
    print(f"  ✓ Created trial subscription: Professional (14 days)")

    db.commit()
    return tenant


def main():
    print("\n🌱 Seeding subscription demo data...\n")
    
    db = SessionLocal()
    try:
        print("📦 Seeding plans...")
        seed_plans(db)
        
        print("\n🏢 Creating demo tenant...")
        tenant = seed_demo_tenant(db)
        
        if tenant:
            print(f"\n✅ Demo data created successfully!")
            print(f"   Tenant: {tenant.name}")
            print(f"   Slug: {tenant.slug}")
        else:
            print("\n⚠️  Could not create demo tenant")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    print("\n🎉 Done!\n")


if __name__ == "__main__":
    main()
