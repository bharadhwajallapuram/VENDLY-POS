"""
Vendly POS - Multi-Store & Transfer API
========================================
Store management, inter-store transfers, franchise analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.subscription_models import Store, Tenant, TenantUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stores", tags=["stores"])


# ============================================
# Schemas
# ============================================


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    timezone: Optional[str] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    code: str
    email: Optional[str]
    phone: Optional[str]
    address_line1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str
    timezone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StoreWithStats(StoreResponse):
    total_sales: float = 0.0
    transaction_count: int = 0
    inventory_value: float = 0.0
    staff_count: int = 0


class TransferItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class TransferCreate(BaseModel):
    from_store_id: int
    to_store_id: int
    items: List[TransferItemCreate]
    priority: str = "normal"
    reason: Optional[str] = None
    notes: Optional[str] = None
    expected_delivery: Optional[datetime] = None


class TransferItemResponse(BaseModel):
    id: int
    product_id: int
    quantity_requested: int
    quantity_sent: Optional[int]
    quantity_received: Optional[int]
    unit_cost: float
    total_value: float
    notes: Optional[str]

    class Config:
        from_attributes = True


class TransferResponse(BaseModel):
    id: int
    transfer_number: str
    from_store_id: int
    to_store_id: int
    status: str
    priority: str
    reason: Optional[str]
    notes: Optional[str]
    requested_by_id: int
    approved_by_id: Optional[int]
    total_items: int
    total_quantity: int
    total_value: float
    requested_at: datetime
    approved_at: Optional[datetime]
    shipped_at: Optional[datetime]
    received_at: Optional[datetime]
    tracking_number: Optional[str]
    carrier: Optional[str]

    class Config:
        from_attributes = True


class TransferWithItems(TransferResponse):
    items: List[TransferItemResponse] = []
    from_store: Optional[StoreResponse] = None
    to_store: Optional[StoreResponse] = None


class StoreComparisonRequest(BaseModel):
    store_ids: List[int]
    start_date: datetime
    end_date: datetime
    metrics: List[str] = ["gross_sales", "transaction_count", "avg_transaction_value"]


class StoreMetrics(BaseModel):
    store_id: int
    store_name: str
    gross_sales: float = 0.0
    net_sales: float = 0.0
    transaction_count: int = 0
    avg_transaction_value: float = 0.0
    items_sold: int = 0
    refund_count: int = 0
    refund_amount: float = 0.0
    unique_customers: int = 0


# ============================================
# Helper Functions
# ============================================


def get_user_tenant(db: Session, user_id: int) -> Optional[Tenant]:
    """Get the tenant for a user"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user_id, TenantUser.is_active == True)
        .first()
    )
    if tenant_user:
        return db.query(Tenant).filter(Tenant.id == tenant_user.tenant_id).first()
    return None


def get_user_stores(db: Session, user_id: int) -> List[Store]:
    """Get stores accessible to a user"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user_id, TenantUser.is_active == True)
        .first()
    )

    if not tenant_user:
        return []

    # If store_ids is null, user has access to all tenant stores
    if not tenant_user.store_ids:
        return (
            db.query(Store)
            .filter(Store.tenant_id == tenant_user.tenant_id, Store.is_active == True)
            .all()
        )

    # Parse store_ids JSON and filter
    try:
        store_ids = json.loads(tenant_user.store_ids)
        return (
            db.query(Store)
            .filter(Store.id.in_(store_ids), Store.is_active == True)
            .all()
        )
    except (json.JSONDecodeError, TypeError):
        return []


def generate_transfer_number(db: Session, tenant_id: int) -> str:
    """Generate unique transfer number"""
    from app.db.multistore_models import StoreTransfer

    today = datetime.utcnow().strftime("%Y%m%d")

    # Count today's transfers for this tenant
    count = (
        db.query(func.count(StoreTransfer.id))
        .filter(
            StoreTransfer.tenant_id == tenant_id,
            func.date(StoreTransfer.requested_at) == datetime.utcnow().date(),
        )
        .scalar()
        or 0
    )

    return f"TRF-{today}-{count + 1:04d}"


# ============================================
# Store Management Endpoints
# ============================================


@router.get("", response_model=List[StoreWithStats])
def list_stores(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all stores accessible to the current user with stats"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    query = db.query(Store).filter(Store.tenant_id == tenant.id)
    if not include_inactive:
        query = query.filter(Store.is_active == True)

    stores = query.all()

    # Add stats (placeholder - in real implementation, aggregate from sales/inventory)
    result = []
    for store in stores:
        store_data = StoreWithStats.model_validate(store)
        # TODO: Calculate real stats from sales and inventory tables
        store_data.total_sales = 0.0
        store_data.transaction_count = 0
        store_data.inventory_value = 0.0
        store_data.staff_count = 0
        result.append(store_data)

    return result


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(
    store_data: StoreCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new store"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Check plan limits
    from app.db.subscription_models import Plan, Subscription

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.tenant_id == tenant.id,
            Subscription.status.in_(["active", "trialing"]),
        )
        .first()
    )

    if subscription:
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if plan:
            current_store_count = (
                db.query(func.count(Store.id))
                .filter(Store.tenant_id == tenant.id, Store.is_active == True)
                .scalar()
                or 0
            )

            if current_store_count >= plan.max_stores:
                raise HTTPException(
                    status_code=400,
                    detail=f"Store limit reached ({plan.max_stores}). Upgrade your plan to add more stores.",
                )

    # Check if code is unique within tenant
    existing = (
        db.query(Store)
        .filter(Store.tenant_id == tenant.id, Store.code == store_data.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Store code already exists")

    store = Store(tenant_id=tenant.id, **store_data.model_dump())
    db.add(store)
    db.commit()
    db.refresh(store)

    logger.info(f"Store {store.code} created for tenant {tenant.id}")
    return store


@router.get("/{store_id}", response_model=StoreWithStats)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get store details with stats"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    store = (
        db.query(Store)
        .filter(Store.id == store_id, Store.tenant_id == tenant.id)
        .first()
    )

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    store_data = StoreWithStats.model_validate(store)
    # TODO: Calculate real stats
    return store_data


@router.put("/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    update_data: StoreUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update store details"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    store = (
        db.query(Store)
        .filter(Store.id == store_id, Store.tenant_id == tenant.id)
        .first()
    )

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(store, field, value)

    db.commit()
    db.refresh(store)

    return store


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Soft-delete a store (deactivate)"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    store = (
        db.query(Store)
        .filter(Store.id == store_id, Store.tenant_id == tenant.id)
        .first()
    )

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Count active stores - don't allow deletion of last store
    active_count = (
        db.query(func.count(Store.id))
        .filter(Store.tenant_id == tenant.id, Store.is_active == True)
        .scalar()
        or 0
    )

    if active_count <= 1:
        raise HTTPException(
            status_code=400, detail="Cannot delete the last active store"
        )

    store.is_active = False
    db.commit()

    return None


# ============================================
# Store Analytics & Comparison
# ============================================


@router.post("/compare", response_model=List[StoreMetrics])
def compare_stores(
    request: StoreComparisonRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compare metrics across multiple stores"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Verify all stores belong to tenant
    stores = (
        db.query(Store)
        .filter(Store.id.in_(request.store_ids), Store.tenant_id == tenant.id)
        .all()
    )

    if len(stores) != len(request.store_ids):
        raise HTTPException(status_code=400, detail="One or more stores not found")

    results = []
    for store in stores:
        # TODO: Aggregate real data from sales, inventory tables
        # For now, return placeholder data
        metrics = StoreMetrics(
            store_id=store.id,
            store_name=store.name,
            gross_sales=0.0,
            net_sales=0.0,
            transaction_count=0,
            avg_transaction_value=0.0,
            items_sold=0,
            refund_count=0,
            refund_amount=0.0,
            unique_customers=0,
        )
        results.append(metrics)

    return results


@router.get("/{store_id}/analytics")
def get_store_analytics(
    store_id: int,
    period: str = Query("week", pattern="^(day|week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed analytics for a store"""
    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    store = (
        db.query(Store)
        .filter(Store.id == store_id, Store.tenant_id == tenant.id)
        .first()
    )

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Calculate date range
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)

    # TODO: Aggregate real data
    return {
        "store_id": store_id,
        "store_name": store.name,
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "summary": {
            "gross_sales": 0.0,
            "net_sales": 0.0,
            "transaction_count": 0,
            "avg_transaction_value": 0.0,
            "items_sold": 0,
            "unique_customers": 0,
        },
        "trends": {
            "sales_trend": [],  # Daily/hourly breakdown
            "top_products": [],
            "top_categories": [],
            "peak_hours": [],
        },
        "inventory": {
            "total_value": 0.0,
            "low_stock_items": 0,
            "out_of_stock_items": 0,
        },
    }


# ============================================
# Inter-Store Transfers
# ============================================


@router.get("/transfers", response_model=List[TransferResponse])
def list_transfers(
    store_id: Optional[int] = None,
    status: Optional[str] = None,
    direction: Optional[str] = Query(None, pattern="^(incoming|outgoing|all)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List inter-store transfers"""
    from app.db.multistore_models import StoreTransfer

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    query = db.query(StoreTransfer).filter(StoreTransfer.tenant_id == tenant.id)

    if store_id:
        if direction == "incoming":
            query = query.filter(StoreTransfer.to_store_id == store_id)
        elif direction == "outgoing":
            query = query.filter(StoreTransfer.from_store_id == store_id)
        else:
            query = query.filter(
                (StoreTransfer.from_store_id == store_id)
                | (StoreTransfer.to_store_id == store_id)
            )

    if status:
        query = query.filter(StoreTransfer.status == status)

    transfers = (
        query.order_by(StoreTransfer.requested_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return transfers


@router.post(
    "/transfers", response_model=TransferWithItems, status_code=status.HTTP_201_CREATED
)
def create_transfer(
    transfer_data: TransferCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new inter-store transfer request"""
    from app.db.models import Product
    from app.db.multistore_models import (
        StoreTransfer,
        StoreTransferItem,
        TransferHistory,
    )

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Validate stores
    from_store = (
        db.query(Store)
        .filter(Store.id == transfer_data.from_store_id, Store.tenant_id == tenant.id)
        .first()
    )

    to_store = (
        db.query(Store)
        .filter(Store.id == transfer_data.to_store_id, Store.tenant_id == tenant.id)
        .first()
    )

    if not from_store or not to_store:
        raise HTTPException(status_code=404, detail="One or both stores not found")

    if from_store.id == to_store.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same store")

    # Create transfer
    transfer = StoreTransfer(
        tenant_id=tenant.id,
        transfer_number=generate_transfer_number(db, tenant.id),
        from_store_id=from_store.id,
        to_store_id=to_store.id,
        status="pending",
        priority=transfer_data.priority,
        reason=transfer_data.reason,
        notes=transfer_data.notes,
        requested_by_id=current_user.id,
        expected_delivery=transfer_data.expected_delivery,
    )
    db.add(transfer)
    db.flush()  # Get transfer ID

    # Add items
    total_items = 0
    total_quantity = 0
    total_value = 0.0

    for item_data in transfer_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {item_data.product_id} not found"
            )

        item = StoreTransferItem(
            transfer_id=transfer.id,
            product_id=product.id,
            quantity_requested=item_data.quantity,
            unit_cost=float(product.cost_price or 0),
            total_value=float(product.cost_price or 0) * item_data.quantity,
            notes=item_data.notes,
        )
        db.add(item)

        total_items += 1
        total_quantity += item_data.quantity
        total_value += item.total_value

    transfer.total_items = total_items
    transfer.total_quantity = total_quantity
    transfer.total_value = total_value

    # Add history entry
    history = TransferHistory(
        transfer_id=transfer.id,
        action="created",
        from_status=None,
        to_status="pending",
        performed_by_id=current_user.id,
    )
    db.add(history)

    db.commit()
    db.refresh(transfer)

    logger.info(
        f"Transfer {transfer.transfer_number} created from store {from_store.code} to {to_store.code}"
    )

    # Build response
    response = TransferWithItems.model_validate(transfer)
    response.items = [
        TransferItemResponse.model_validate(item) for item in transfer.items
    ]
    response.from_store = StoreResponse.model_validate(from_store)
    response.to_store = StoreResponse.model_validate(to_store)

    return response


@router.get("/transfers/{transfer_id}", response_model=TransferWithItems)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get transfer details"""
    from app.db.multistore_models import StoreTransfer

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    transfer = (
        db.query(StoreTransfer)
        .filter(StoreTransfer.id == transfer_id, StoreTransfer.tenant_id == tenant.id)
        .first()
    )

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    from_store = db.query(Store).filter(Store.id == transfer.from_store_id).first()
    to_store = db.query(Store).filter(Store.id == transfer.to_store_id).first()

    response = TransferWithItems.model_validate(transfer)
    response.items = [
        TransferItemResponse.model_validate(item) for item in transfer.items
    ]
    response.from_store = (
        StoreResponse.model_validate(from_store) if from_store else None
    )
    response.to_store = StoreResponse.model_validate(to_store) if to_store else None

    return response


@router.post("/transfers/{transfer_id}/approve")
def approve_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a pending transfer"""
    from app.db.multistore_models import StoreTransfer, TransferHistory

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    transfer = (
        db.query(StoreTransfer)
        .filter(StoreTransfer.id == transfer_id, StoreTransfer.tenant_id == tenant.id)
        .first()
    )

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if transfer.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve transfer with status '{transfer.status}'",
        )

    # Update status
    old_status = transfer.status
    transfer.status = "approved"
    transfer.approved_by_id = current_user.id
    transfer.approved_at = datetime.utcnow()

    # Add history
    history = TransferHistory(
        transfer_id=transfer.id,
        action="approved",
        from_status=old_status,
        to_status="approved",
        performed_by_id=current_user.id,
    )
    db.add(history)

    db.commit()

    return {"message": "Transfer approved", "transfer_number": transfer.transfer_number}


@router.post("/transfers/{transfer_id}/ship")
def ship_transfer(
    transfer_id: int,
    tracking_number: Optional[str] = None,
    carrier: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark transfer as shipped/in transit"""
    from app.db.multistore_models import StoreTransfer, TransferHistory

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    transfer = (
        db.query(StoreTransfer)
        .filter(StoreTransfer.id == transfer_id, StoreTransfer.tenant_id == tenant.id)
        .first()
    )

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if transfer.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot ship transfer with status '{transfer.status}'",
        )

    old_status = transfer.status
    transfer.status = "in_transit"
    transfer.shipped_at = datetime.utcnow()
    transfer.tracking_number = tracking_number
    transfer.carrier = carrier

    # Update sent quantities to match requested
    for item in transfer.items:
        item.quantity_sent = item.quantity_requested

    history = TransferHistory(
        transfer_id=transfer.id,
        action="shipped",
        from_status=old_status,
        to_status="in_transit",
        performed_by_id=current_user.id,
        notes=f"Tracking: {tracking_number}" if tracking_number else None,
    )
    db.add(history)

    db.commit()

    return {"message": "Transfer shipped", "transfer_number": transfer.transfer_number}


class ReceiveItemData(BaseModel):
    item_id: int
    quantity_received: int
    notes: Optional[str] = None


class ReceiveTransferData(BaseModel):
    items: List[ReceiveItemData]
    notes: Optional[str] = None


@router.post("/transfers/{transfer_id}/receive")
def receive_transfer(
    transfer_id: int,
    receive_data: ReceiveTransferData,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark transfer as received and update inventory"""
    from app.db.multistore_models import StoreInventory, StoreTransfer, TransferHistory

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    transfer = (
        db.query(StoreTransfer)
        .filter(StoreTransfer.id == transfer_id, StoreTransfer.tenant_id == tenant.id)
        .first()
    )

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if transfer.status != "in_transit":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot receive transfer with status '{transfer.status}'",
        )

    # Update item quantities
    for item_data in receive_data.items:
        item = next((i for i in transfer.items if i.id == item_data.item_id), None)
        if item:
            item.quantity_received = item_data.quantity_received
            if item_data.notes:
                item.notes = item_data.notes

            # Update destination store inventory
            # (In a real implementation, also deduct from source store)
            store_inv = (
                db.query(StoreInventory)
                .filter(
                    StoreInventory.store_id == transfer.to_store_id,
                    StoreInventory.product_id == item.product_id,
                )
                .first()
            )

            if store_inv:
                store_inv.quantity += item_data.quantity_received
                store_inv.last_received_at = datetime.utcnow()
            else:
                store_inv = StoreInventory(
                    store_id=transfer.to_store_id,
                    product_id=item.product_id,
                    quantity=item_data.quantity_received,
                    available_quantity=item_data.quantity_received,
                    last_received_at=datetime.utcnow(),
                )
                db.add(store_inv)

    old_status = transfer.status
    transfer.status = "received"
    transfer.received_by_id = current_user.id
    transfer.received_at = datetime.utcnow()

    history = TransferHistory(
        transfer_id=transfer.id,
        action="received",
        from_status=old_status,
        to_status="received",
        performed_by_id=current_user.id,
        notes=receive_data.notes,
    )
    db.add(history)

    db.commit()

    return {"message": "Transfer received", "transfer_number": transfer.transfer_number}


@router.post("/transfers/{transfer_id}/cancel")
def cancel_transfer(
    transfer_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cancel a transfer"""
    from app.db.multistore_models import StoreTransfer, TransferHistory

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    transfer = (
        db.query(StoreTransfer)
        .filter(StoreTransfer.id == transfer_id, StoreTransfer.tenant_id == tenant.id)
        .first()
    )

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if transfer.status in ["received", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel transfer with status '{transfer.status}'",
        )

    old_status = transfer.status
    transfer.status = "cancelled"

    history = TransferHistory(
        transfer_id=transfer.id,
        action="cancelled",
        from_status=old_status,
        to_status="cancelled",
        performed_by_id=current_user.id,
        notes=reason,
    )
    db.add(history)

    db.commit()

    return {
        "message": "Transfer cancelled",
        "transfer_number": transfer.transfer_number,
    }
