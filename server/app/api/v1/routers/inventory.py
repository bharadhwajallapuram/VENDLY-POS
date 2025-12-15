"""
Vendly POS - Inventory Routes
==============================
API endpoints for inventory management and tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.core.deps import get_db, get_current_user
from app.core.permissions import Permission
from app.services.inventory import InventoryService
from app.db import models as m
from app.services.ws_manager import manager

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/summary")
async def get_inventory_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get overall inventory statistics
    
    Returns:
        - total_products: Total active products
        - in_stock: Products with quantity > 0
        - out_of_stock: Products with quantity = 0
        - low_stock: Products below minimum quantity
        - total_quantity: Sum of all quantities
        - total_value: Total inventory value
    """
    summary = InventoryService.get_inventory_summary(db)
    return summary


@router.get("/low-stock")
async def get_low_stock_products(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    threshold: Optional[int] = Query(None, ge=0, le=100000, description="Custom low stock threshold (0-100000)")
):
    """
    Get all products below minimum quantity
    
    Query Parameters:
        - threshold: Optional custom threshold (overrides product.min_quantity)
    
    Returns:
        List of low stock products with shortage amounts
    """
    products = InventoryService.get_low_stock_products(db, threshold)
    return {
        "count": len(products),
        "items": products
    }


@router.get("/out-of-stock")
async def get_out_of_stock_products(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get all products with zero quantity
    
    Returns:
        List of out of stock products
    """
    products = InventoryService.get_out_of_stock_products(db)
    return {
        "count": len(products),
        "items": products
    }


@router.post("/adjust/{product_id}")
async def adjust_inventory(
    product_id: int,
    quantity_change: int = Query(..., ge=-10000, le=10000, description="Change in quantity (-10000 to 10000)"),
    reason: str = Query("adjustment", min_length=1, max_length=100, description="Reason for adjustment (1-100 chars)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Manually adjust product inventory
    
    Query Parameters:
        - quantity_change: Amount to change (positive or negative)
        - reason: Reason for adjustment
    
    Returns:
        Updated product information
    """
    product = await InventoryService.update_inventory(
        db,
        product_id,
        quantity_change,
        reason=reason,
        broadcast=True
    )
    
    if not product:
        raise HTTPException(404, detail="Product not found")
    
    db.commit()
    
    return {
        "id": product.id,
        "name": product.name,
        "quantity": product.quantity,
        "min_quantity": product.min_quantity,
        "change": quantity_change,
        "reason": reason,
        "timestamp": product.updated_at.isoformat() if product.updated_at else None
    }


@router.post("/set/{product_id}")
async def set_inventory(
    product_id: int,
    quantity: int = Query(..., ge=0, le=1000000, description="New quantity (0-1000000)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Set inventory to exact quantity (stock count)
    
    Query Parameters:
        - quantity: New quantity value
    
    Returns:
        Updated product information
    """
    product = db.get(m.Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")
    
    old_qty = product.quantity
    change = quantity - old_qty
    
    await InventoryService.update_inventory(
        db,
        product_id,
        change,
        reason="stock_count",
        broadcast=True
    )
    
    db.commit()
    
    return {
        "id": product.id,
        "name": product.name,
        "previous_quantity": old_qty,
        "new_quantity": quantity,
        "change": change,
        "reason": "stock_count",
        "timestamp": product.updated_at.isoformat() if product.updated_at else None
    }


@router.get("/history/{product_id}")
async def get_inventory_history(
    product_id: int,
    days: int = Query(7, ge=1, le=90, description="Days to look back"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get inventory change history for a product
    
    Query Parameters:
        - days: Number of days to look back (1-90, default 7)
    
    Returns:
        List of inventory transactions
    """
    # Verify product exists
    product = db.get(m.Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")
    
    history = InventoryService.get_inventory_history(db, product_id, days)
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "days": days,
        "count": len(history),
        "items": history
    }


@router.post("/alert-check/{product_id}")
async def check_and_alert_low_stock(
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Check if product is low stock and send alert if needed
    
    Returns:
        - alert_sent: Whether an alert was sent
        - status: 'normal', 'low_stock', 'out_of_stock'
    """
    product = db.get(m.Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")
    
    alert_sent = await InventoryService.check_and_alert_low_stock(db, product_id)
    
    if product.quantity == 0:
        status = "out_of_stock"
    elif product.quantity <= product.min_quantity:
        status = "low_stock"
    else:
        status = "normal"
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "quantity": product.quantity,
        "min_quantity": product.min_quantity,
        "status": status,
        "alert_sent": alert_sent
    }


@router.websocket("/ws")
async def websocket_inventory_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time inventory updates
    
    Clients can connect to /api/v1/inventory/ws to receive live inventory
    updates when products are added, updated, or stock levels change.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)