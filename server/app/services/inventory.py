"""
Vendly POS - Inventory Service
===============================
Inventory management with real-time updates and low-stock alerts
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.websocket import InventoryUpdateData, WSEventType, ws_manager
from app.db import models as m

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for inventory management and tracking"""

    @staticmethod
    async def update_inventory(
        db: Session,
        product_id: int,
        quantity_change: int,
        reason: str = "adjustment",
        broadcast: bool = True,
    ) -> Optional[m.Product]:
        """
        Update product inventory with real-time broadcast

        Args:
            db: Database session
            product_id: Product ID
            quantity_change: Change in quantity (can be negative)
            reason: Reason for change ('sale', 'adjustment', 'restock', 'return')
            broadcast: Whether to broadcast update via WebSocket

        Returns:
            Updated product or None if not found
        """
        product = db.get(m.Product, product_id)

        if not product:
            logger.warning(f"Product {product_id} not found for inventory update")
            return None

        previous_qty = product.quantity
        new_qty = max(0, previous_qty + quantity_change)  # Don't go below 0
        product.quantity = new_qty
        product.updated_at = datetime.utcnow()

        db.add(product)
        db.flush()

        # Broadcast real-time update
        if broadcast:
            update_data = InventoryUpdateData(
                product_id=product.id,
                product_name=product.name,
                previous_qty=previous_qty,
                new_qty=new_qty,
                reason=reason,
                min_qty=product.min_quantity,
            )

            await ws_manager.broadcast_inventory_update(update_data)

            # Log low stock/out of stock
            if update_data.is_out_of_stock:
                logger.warning(
                    f"Product {product.name} ({product.id}) is now OUT OF STOCK"
                )
            elif update_data.is_low_stock:
                logger.warning(
                    f"Product {product.name} ({product.id}) is LOW STOCK: {new_qty}/{product.min_quantity}"
                )

        return product

    @staticmethod
    def get_low_stock_products(
        db: Session, threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all products below minimum quantity

        Args:
            db: Database session
            threshold: Custom threshold (uses product.min_quantity if None)

        Returns:
            List of low stock product info
        """
        query = db.query(m.Product).filter(m.Product.is_active == True)

        products = query.all()
        result = []

        for product in products:
            # Check if product is low stock
            if threshold is not None:
                is_low = product.quantity <= threshold
            else:
                is_low = (
                    product.quantity <= product.min_quantity
                    and product.min_quantity > 0
                )

            if is_low:
                result.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "barcode": product.barcode,
                        "current_qty": product.quantity,
                        "min_qty": product.min_quantity,
                        "shortage": (
                            product.min_quantity - product.quantity
                            if product.min_quantity > product.quantity
                            else 0
                        ),
                        "category_id": product.category_id,
                        "price": float(product.price),
                        "cost": float(product.cost) if product.cost else 0,
                        "updated_at": (
                            product.updated_at.isoformat()
                            if product.updated_at
                            else None
                        ),
                    }
                )

        return sorted(result, key=lambda x: x["shortage"], reverse=True)

    @staticmethod
    def get_out_of_stock_products(db: Session) -> List[Dict[str, Any]]:
        """
        Get all products with zero quantity

        Returns:
            List of out of stock product info
        """
        products = (
            db.query(m.Product)
            .filter(m.Product.quantity == 0, m.Product.is_active == True)
            .all()
        )

        return [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "barcode": p.barcode,
                "category_id": p.category_id,
                "price": float(p.price),
                "cost": float(p.cost) if p.cost else 0,
                "min_qty": p.min_quantity,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in products
        ]

    @staticmethod
    def get_inventory_summary(db: Session) -> Dict[str, Any]:
        """
        Get overall inventory statistics

        Returns:
            Inventory summary with counts and values
        """
        products = db.query(m.Product).filter(m.Product.is_active == True).all()

        total_products = len(products)
        out_of_stock = sum(1 for p in products if p.quantity == 0)
        low_stock = sum(
            1 for p in products if p.quantity <= p.min_quantity and p.quantity > 0
        )
        total_qty = sum(p.quantity for p in products)
        total_value = sum((p.cost or p.price) * p.quantity for p in products)

        return {
            "total_products": total_products,
            "in_stock": total_products - out_of_stock,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "total_quantity": total_qty,
            "total_value": float(total_value),
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_inventory_history(
        db: Session, product_id: Optional[int] = None, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get inventory change history from InventoryMovement table.

        Args:
            db: Database session
            product_id: Filter by product ID (optional)
            days: Number of days to look back

        Returns:
            List of inventory changes with product info
        """
        # Calculate the date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)

        # Build query using InventoryMovement model
        query = db.query(m.InventoryMovement).filter(
            m.InventoryMovement.created_at >= date_threshold
        )

        # Filter by product if specified
        if product_id is not None:
            query = query.filter(m.InventoryMovement.product_id == product_id)

        # Order by most recent first
        movements = query.order_by(m.InventoryMovement.created_at.desc()).all()

        # Transform to dictionary format with product info
        result = []
        for movement in movements:
            product = db.get(m.Product, movement.product_id)
            result.append({
                "id": movement.id,
                "product_id": movement.product_id,
                "product_name": product.name if product else "Unknown",
                "quantity_change": movement.quantity_change,
                "movement_type": movement.movement_type,
                "reference_id": movement.reference_id,
                "notes": movement.notes,
                "user_id": movement.user_id,
                "created_at": movement.created_at.isoformat() if movement.created_at else None,
            })

        return result

    @staticmethod
    async def check_and_alert_low_stock(db: Session, product_id: int) -> bool:
        """
        Check if product is low stock and send alert

        Args:
            db: Database session
            product_id: Product to check

        Returns:
            True if low stock alert was sent
        """
        product = db.get(m.Product, product_id)

        if not product:
            return False

        is_low_stock = product.quantity <= product.min_quantity and product.quantity > 0
        is_out_of_stock = product.quantity == 0

        if is_out_of_stock:
            await ws_manager.broadcast_notification(
                title="Out of Stock Alert",
                message=f"{product.name} is out of stock!",
                severity="error",
            )
            return True

        elif is_low_stock:
            shortage = product.min_quantity - product.quantity
            await ws_manager.broadcast_notification(
                title="Low Stock Alert",
                message=f"{product.name}: {product.quantity} units remaining (need {shortage} more)",
                severity="warning",
            )
            return True

        return False

    @staticmethod
    def validate_quantity(
        product: m.Product, required_qty: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if product has sufficient quantity

        Args:
            product: Product to check
            required_qty: Required quantity

        Returns:
            Tuple of (is_valid, error_message)
        """
        if product.quantity < required_qty:
            shortage = required_qty - product.quantity
            return False, f"Insufficient stock. Need {shortage} more units."

        return True, None

    @staticmethod
    async def process_sale_inventory(
        db: Session, sale_items: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Process inventory for a sale (reduce quantities)

        Args:
            db: Database session
            sale_items: List of items with product_id and quantity

        Returns:
            Tuple of (success, error_message)
        """
        try:
            for item in sale_items:
                product_id_raw: Any = item.get("product_id")
                product_id: int = (
                    int(product_id_raw)
                    if product_id_raw and isinstance(product_id_raw, (int, float))
                    else 0
                )

                if product_id <= 0:
                    return False, "Invalid product_id in sale_items"

                qty_raw: Any = item.get("quantity")
                qty: int = (
                    int(qty_raw) if qty_raw and isinstance(qty_raw, (int, float)) else 0
                )

                product = db.get(m.Product, product_id)
                if not product:
                    return False, f"Product {product_id} not found"

                is_valid, error_msg = InventoryService.validate_quantity(product, qty)
                if not is_valid:
                    return False, error_msg

                # Update inventory
                await InventoryService.update_inventory(
                    db, product_id, -qty, reason="sale", broadcast=True
                )

            return True, None

        except Exception as e:
            logger.error(f"Error processing sale inventory: {e}")
            return False, str(e)

    @staticmethod
    async def process_return_inventory(
        db: Session, product_id: int, quantity: int, reason: str = "return"
    ) -> Tuple[bool, Optional[str]]:
        """
        Process inventory for a return (increase quantity)

        Args:
            db: Database session
            product_id: Product to return
            quantity: Quantity to return
            reason: Reason for increase

        Returns:
            Tuple of (success, error_message)
        """
        try:
            product = db.get(m.Product, product_id)
            if not product:
                return False, f"Product {product_id} not found"

            await InventoryService.update_inventory(
                db, product_id, quantity, reason=reason, broadcast=True
            )

            return True, None

        except Exception as e:
            logger.error(f"Error processing return inventory: {e}")
            return False, str(e)


# Export for easy access
__all__ = ["InventoryService"]
