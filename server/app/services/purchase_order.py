from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import Product, PurchaseOrder
from app.services.inventory import InventoryService


class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_purchase_order(
        self,
        product_id: int,
        quantity: int,
        supplier_notes: Optional[str] = None,
        status: str = "pending",
    ) -> PurchaseOrder:
        """Create a new purchase order"""
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        order = PurchaseOrder(
            product_id=product_id,
            product_name=product.name,
            quantity=quantity,
            supplier_notes=supplier_notes,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> list[PurchaseOrder]:
        """List purchase orders"""
        query = self.db.query(PurchaseOrder).order_by(desc(PurchaseOrder.created_at))

        if status:
            query = query.filter(PurchaseOrder.status == status)

        return query.offset(skip).limit(limit).all()

    def get_purchase_order(self, order_id: int) -> Optional[PurchaseOrder]:
        """Get a specific purchase order"""
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()

    async def update_status(self, order_id: int, status: str) -> Optional[PurchaseOrder]:
        """Update purchase order status"""
        valid_statuses = ["pending", "ordered", "received", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        order = (
            self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        )
        if not order:
            return None

        order.status = status
        order.updated_at = datetime.utcnow()

        # If received, update inventory and broadcast the change
        if status == "received":
            await InventoryService.update_inventory(
                self.db,
                order.product_id,
                order.quantity,
                reason=f"Purchase order #{order_id} received",
                broadcast=True,
            )

        self.db.commit()
        self.db.refresh(order)
        return order
