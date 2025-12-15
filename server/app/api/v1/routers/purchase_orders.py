"""
Purchase Orders Router
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderResponse
from app.services.purchase_order import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

@router.post("", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    order_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
):
    """Create a new purchase order"""
    try:
        service = PurchaseOrderService(db)
        order = service.create_purchase_order(
            product_id=order_data.product_id,
            quantity=order_data.quantity,
            supplier_notes=order_data.supplier_notes,
            status=order_data.status or "pending",
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating purchase order: {str(e)}")

@router.get("", response_model=list[PurchaseOrderResponse])
async def list_purchase_orders(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List all purchase orders"""
    service = PurchaseOrderService(db)
    orders = service.list_purchase_orders(skip=skip, limit=limit, status=status)
    return orders

@router.get("/{order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific purchase order"""
    service = PurchaseOrderService(db)
    order = service.get_purchase_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order

@router.patch("/{order_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    """Update purchase order status (received, cancelled, etc.)"""
    try:
        service = PurchaseOrderService(db)
        order = await service.update_status(order_id, status)
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
