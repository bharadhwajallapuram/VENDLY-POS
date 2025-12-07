"""
Vendly POS - Sales Router
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.api.v1.schemas.sales import SaleIn, SaleItemOut, SaleOut
from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.services.receipt import (
    Receipt,
    ReceiptItem,
    generate_receipt_html,
    generate_receipt_text,
)
from app.services.ws_manager import manager

router = APIRouter()


@router.get("", response_model=List[SaleOut])
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all sales with optional filtering"""
    stmt = db.query(m.Sale)
    if status:
        stmt = stmt.filter(m.Sale.status == status)
    sales = stmt.order_by(m.Sale.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to output format
    result = []
    for sale in sales:
        items = []
        for item in sale.items:
            product = db.get(m.Product, item.product_id)
            items.append(
                SaleItemOut(
                    id=item.id,
                    sale_id=item.sale_id,
                    product_id=item.product_id,
                    product_name=product.name if product else None,
                    quantity=item.quantity,
                    unit_price=float(item.unit_price),
                    discount=float(item.discount),
                    total=float(item.subtotal),
                )
            )
        result.append(
            SaleOut(
                id=sale.id,
                user_id=sale.user_id,
                customer_id=sale.customer_id,
                subtotal=float(sale.subtotal),
                tax=float(sale.tax),
                discount=float(sale.discount),
                total=float(sale.total),
                payment_method=sale.payment_method,
                payment_reference=sale.payment_reference,
                status=sale.status,
                notes=sale.notes,
                created_at=sale.created_at,
                items=items,
            )
        )
    return result


@router.post("", response_model=SaleOut, status_code=201)
def create_sale(
    payload: SaleIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new sale (checkout)"""
    # Calculate totals
    subtotal = 0.0
    tax = 0.0

    for item in payload.items:
        product = db.get(m.Product, item.product_id)
        if not product:
            raise HTTPException(400, detail=f"Product {item.product_id} not found")
        if product.quantity < item.quantity:
            raise HTTPException(400, detail=f"Insufficient stock for {product.name}")

        item_total = (item.unit_price * item.quantity) - item.discount
        subtotal += item_total
        tax += item_total * float(product.tax_rate) / 100

    total = subtotal + tax - payload.discount

    # Create sale
    sale = m.Sale(
        user_id=user.id,
        customer_id=payload.customer_id,
        subtotal=subtotal,
        tax=tax,
        discount=payload.discount,
        total=total,
        payment_method=payload.payment_method,
        payment_reference=payload.payment_reference,
        status="completed",
        notes=payload.notes,
    )
    db.add(sale)
    db.flush()  # Get sale.id

    # Create sale items and update inventory
    sale_items: list[m.SaleItem] = []
    for item in payload.items:
        product = db.get(m.Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} not found"
            )
        item_total = (item.unit_price * item.quantity) - item.discount

        sale_item = m.SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            subtotal=item_total,
        )
        db.add(sale_item)
        sale_items.append(sale_item)

        # Reduce inventory
        product.quantity -= item.quantity

    db.commit()
    db.refresh(sale)

    # Build response
    items_out = []
    for i, sale_item in enumerate(sale_items):
        product = db.get(m.Product, sale_item.product_id)
        items_out.append(
            SaleItemOut(
                id=sale_item.id,
                sale_id=sale.id,
                product_id=sale_item.product_id,
                product_name=product.name if product else None,
                quantity=sale_item.quantity,
                unit_price=float(sale_item.unit_price),
                discount=float(sale_item.discount),
                total=float(sale_item.subtotal),
            )
        )

    # Broadcast sale completed
    try:
        import anyio

        anyio.from_thread.run(
            manager.broadcast,
            {
                "event": "sale.completed",
                "sale_id": sale.id,
                "total": float(sale.total),
            },
        )
    except Exception:
        pass

    return SaleOut(
        id=sale.id,
        user_id=sale.user_id,
        customer_id=sale.customer_id,
        subtotal=float(sale.subtotal),
        tax=float(sale.tax),
        discount=float(sale.discount),
        total=float(sale.total),
        payment_method=sale.payment_method,
        payment_reference=sale.payment_reference,
        status=sale.status,
        notes=sale.notes,
        created_at=sale.created_at,
        items=items_out,
    )


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a single sale by ID"""
    sale = db.get(m.Sale, sale_id)
    if not sale:
        raise HTTPException(404, detail="Sale not found")

    items = []
    for item in sale.items:
        product = db.get(m.Product, item.product_id)
        items.append(
            SaleItemOut(
                id=item.id,
                sale_id=item.sale_id,
                product_id=item.product_id,
                product_name=product.name if product else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                discount=float(item.discount),
                total=float(item.subtotal),
            )
        )

    return SaleOut(
        id=sale.id,
        user_id=sale.user_id,
        customer_id=sale.customer_id,
        subtotal=float(sale.subtotal),
        tax=float(sale.tax),
        discount=float(sale.discount),
        total=float(sale.total),
        payment_method=sale.payment_method,
        payment_reference=sale.payment_reference,
        status=sale.status,
        notes=sale.notes,
        created_at=sale.created_at,
        items=items,
    )


@router.post("/{sale_id}/void", response_model=SaleOut)
def void_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Void a sale and restore inventory"""
    sale = db.get(m.Sale, sale_id)
    if not sale:
        raise HTTPException(404, detail="Sale not found")
    if sale.status != "completed":
        raise HTTPException(400, detail="Can only void completed sales")

    # Restore inventory
    for item in sale.items:
        product = db.get(m.Product, item.product_id)
        if product:
            product.quantity += item.quantity

    sale.status = "voided"
    db.commit()
    db.refresh(sale)

    items = []
    for item in sale.items:
        product = db.get(m.Product, item.product_id)
        items.append(
            SaleItemOut(
                id=item.id,
                sale_id=item.sale_id,
                product_id=item.product_id,
                product_name=product.name if product else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                discount=float(item.discount),
                total=float(item.subtotal),
            )
        )

    return SaleOut(
        id=sale.id,
        user_id=sale.user_id,
        customer_id=sale.customer_id,
        subtotal=float(sale.subtotal),
        tax=float(sale.tax),
        discount=float(sale.discount),
        total=float(sale.total),
        payment_method=sale.payment_method,
        payment_reference=sale.payment_reference,
        status=sale.status,
        notes=sale.notes,
        created_at=sale.created_at,
        items=items,
    )


@router.get("/{sale_id}/receipt")
def get_receipt(
    sale_id: int,
    format: str = Query("html", pattern="^(text|html)$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get a printable receipt for a sale.
    Format can be 'text' (for thermal printers) or 'html' (for regular printers)
    """
    sale = db.get(m.Sale, sale_id)
    if not sale:
        raise HTTPException(404, detail="Sale not found")

    # Build receipt items
    receipt_items = []
    for item in sale.items:
        product = db.get(m.Product, item.product_id)
        receipt_items.append(
            ReceiptItem(
                name=product.name if product else f"Product #{item.product_id}",
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                total=float(item.subtotal),
            )
        )

    # Get cashier name
    cashier = db.get(m.User, sale.user_id)
    cashier_name = cashier.full_name or cashier.email if cashier else "Unknown"

    # Get customer if any
    customer_name = None
    if sale.customer_id:
        customer = db.get(m.Customer, sale.customer_id)
        customer_name = customer.name if customer else None

    # Calculate tax rate (assume 8% if not stored)
    tax_rate = 8.0
    if sale.subtotal > 0:
        tax_rate = round((float(sale.tax) / float(sale.subtotal)) * 100, 2)

    # Build receipt object
    receipt = Receipt(
        receipt_number=f"R-{sale.id:06d}",
        date=sale.created_at,
        items=receipt_items,
        subtotal=float(sale.subtotal),
        tax_amount=float(sale.tax),
        tax_rate=tax_rate,
        total=float(sale.total),
        payment_method=sale.payment_method or "cash",
        amount_paid=float(sale.total),  # Assuming exact payment for now
        change=0.0,
        cashier_name=cashier_name,
        customer_name=customer_name,
    )

    if format == "text":
        receipt_content = generate_receipt_text(receipt)
        return PlainTextResponse(content=receipt_content)
    else:
        receipt_content = generate_receipt_html(receipt)
        return HTMLResponse(content=receipt_content)
