from fastapi import APIRouter

from . import (  # demand_forecast,  # Temporarily disabled due to ai_ml dependency
    ai,
    auth,
    backups,
    coupons,
    customers,
    health,
    integrations,
    inventory,
    legal,
    payments,
    peripherals,
    products,
    purchase_orders,
    reports,
    sales,
    tax,
    two_factor_auth,
    users,
    websocket,
    ws,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(two_factor_auth.router, prefix="/auth", tags=["2fa"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    inventory.router, tags=["inventory"]
)  # Has prefix in router itself
api_router.include_router(
    websocket.router, tags=["websocket"]
)  # Has prefix in router itself
api_router.include_router(ws.router, tags=["websocket"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(purchase_orders.router, tags=["purchase-orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["coupons"])
api_router.include_router(backups.router, tags=["backups"])
api_router.include_router(integrations.router, tags=["integrations"])
api_router.include_router(peripherals.router, tags=["peripherals"])
api_router.include_router(tax.router, tags=["tax"])
api_router.include_router(legal.router, tags=["legal"])
# api_router.include_router(demand_forecast.router, tags=["demand-forecast"])  # Temporarily disabled
