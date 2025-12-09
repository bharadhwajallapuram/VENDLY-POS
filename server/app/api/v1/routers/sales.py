"""
Vendly POS - Sales Router
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.schemas.refund import RefundItem, RefundRequest, RefundResponse
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


# Simple in-memory coupons/promotions
# Types: "percent" (value=percent off) or "amount" (value=fixed dollars off)
# max_off caps the discount for percent coupons
COUPONS = {
    "SAVE10": {"type": "percent", "value": 10},
    "WELCOME15": {"type": "percent", "value": 15, "max_off": 25},
    "FLAT5": {"type": "amount", "value": 5},
}


# Refund endpoint (partial/full)
@router.post("/{sale_id}/refund", response_model=RefundResponse)
def refund_sale(
    sale_id: int,
    payload: RefundRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate employee ID
    if not payload.employee_id or not payload.employee_id.strip():
        raise HTTPException(400, detail="Employee ID is required for refund processing")

    # Verify employee exists (check by ID or email)
    if payload.employee_id.isdigit():
        employee = (
            db.query(m.User)
            .filter(
                or_(
                    m.User.id == int(payload.employee_id),
                    m.User.email == payload.employee_id,
                )
            )
            .first()
        )
    else:
        employee = db.query(m.User).filter(m.User.email == payload.employee_id).first()
    if not employee:
        raise HTTPException(400, detail="Invalid Employee ID")
    if not employee.is_active:
        raise HTTPException(400, detail="Employee account is inactive")

    sale = db.get(m.Sale, sale_id)
    if not sale:
        raise HTTPException(404, detail="Sale not found")
    if sale.status not in ("completed", "partially_refunded"):
        raise HTTPException(400, detail="Can only refund completed sales")

    total_refund = 0.0
    refunded_items = []
    for item in payload.items:
        sale_item = db.get(m.SaleItem, item.sale_item_id)
        if not sale_item or sale_item.sale_id != sale_id:
            raise HTTPException(
                400, detail=f"Sale item {item.sale_item_id} not found in sale"
            )
        if item.quantity > sale_item.quantity:
            raise HTTPException(
                400, detail=f"Cannot refund more than sold for item {sale_item.id}"
            )
        # Restore inventory
        product = db.get(m.Product, sale_item.product_id)
        if product:
            product.quantity += item.quantity
        # Calculate refund amount (convert Decimal to float)
        unit_price = float(sale_item.unit_price) if sale_item.unit_price else 0.0
        discount = float(sale_item.discount) if sale_item.discount else 0.0
        refund_amount = (unit_price - discount) * item.quantity
        total_refund += refund_amount
        refunded_items.append(
            {"sale_item_id": item.sale_item_id, "quantity": item.quantity}
        )
        # Reduce sale item quantity
        sale_item.quantity -= item.quantity
        sale_item.subtotal = float(sale_item.subtotal or 0) - refund_amount
    # Update sale status
    if all(si.quantity == 0 for si in sale.items):
        sale.status = "refunded"
    else:
        sale.status = "partially_refunded"
    db.commit()
    db.refresh(sale)
    return RefundResponse(
        sale_id=sale.id,
        refunded_items=[RefundItem(**ri) for ri in refunded_items],
        status=sale.status,
        refund_amount=round(total_refund, 2),
        processed_by=payload.employee_id,
        message=f"Refund processed successfully by employee {employee.email}.",
    )


# Return endpoint (items returned to inventory, customer gets refund)
@router.post("/{sale_id}/return", response_model=RefundResponse)
def return_sale(
    sale_id: int,
    payload: RefundRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate employee ID
    if not payload.employee_id or not payload.employee_id.strip():
        raise HTTPException(400, detail="Employee ID is required for return processing")

    # Verify employee exists (check by ID or email)
    if payload.employee_id.isdigit():
        employee = (
            db.query(m.User)
            .filter(
                or_(
                    m.User.id == int(payload.employee_id),
                    m.User.email == payload.employee_id,
                )
            )
            .first()
        )
    else:
        employee = db.query(m.User).filter(m.User.email == payload.employee_id).first()
    if not employee:
        raise HTTPException(400, detail="Invalid Employee ID")
    if not employee.is_active:
        raise HTTPException(400, detail="Employee account is inactive")

    sale = db.get(m.Sale, sale_id)
    if not sale:
        raise HTTPException(404, detail="Sale not found")
    if sale.status not in ("completed", "partially_refunded", "partially_returned"):
        raise HTTPException(400, detail="Can only return items from completed sales")

    total_return = 0.0
    returned_items = []
    for item in payload.items:
        sale_item = db.get(m.SaleItem, item.sale_item_id)
        if not sale_item or sale_item.sale_id != sale_id:
            raise HTTPException(
                400, detail=f"Sale item {item.sale_item_id} not found in sale"
            )
        if item.quantity > sale_item.quantity:
            raise HTTPException(
                400, detail=f"Cannot return more than sold for item {sale_item.id}"
            )
        # Restore inventory
        product = db.get(m.Product, sale_item.product_id)
        if product:
            product.quantity += item.quantity
        # Calculate return amount (convert Decimal to float)
        unit_price = float(sale_item.unit_price) if sale_item.unit_price else 0.0
        discount = float(sale_item.discount) if sale_item.discount else 0.0
        return_amount = (unit_price - discount) * item.quantity
        total_return += return_amount
        returned_items.append(
            {"sale_item_id": item.sale_item_id, "quantity": item.quantity}
        )
        # Reduce sale item quantity
        sale_item.quantity -= item.quantity
        sale_item.subtotal = float(sale_item.subtotal or 0) - return_amount
    # Update sale status
    if all(si.quantity == 0 for si in sale.items):
        sale.status = "returned"
    else:
        sale.status = "partially_returned"
    db.commit()
    db.refresh(sale)
    return RefundResponse(
        sale_id=sale.id,
        refunded_items=[RefundItem(**ri) for ri in returned_items],
        status=sale.status,
        refund_amount=round(total_return, 2),
        processed_by=payload.employee_id,
        message=f"Return processed successfully by employee {employee.email}.",
    )


@router.get("", response_model=List[SaleOut])
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    customer_phone: Optional[str] = Query(None),
    customer_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all sales with optional filtering by status, customer phone, or customer name"""
    stmt = db.query(m.Sale)
    if status:
        stmt = stmt.filter(m.Sale.status == status)
    if customer_phone or customer_name:
        stmt = stmt.join(m.Customer, m.Sale.customer_id == m.Customer.id)
        if customer_phone:
            stmt = stmt.filter(m.Customer.phone.ilike(f"%{customer_phone}%"))
        if customer_name:
            stmt = stmt.filter(m.Customer.name.ilike(f"%{customer_name}%"))
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
                order_discount=float(getattr(sale, "order_discount", 0) or 0),
                coupon_discount=float(getattr(sale, "coupon_discount", 0) or 0),
                coupon_code=getattr(sale, "coupon_code", None),
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

    # Validate coupon (if provided)
    coupon_code = (payload.coupon_code or "").strip().upper() or None
    coupon_discount = 0.0
    if coupon_code:
        coupon = COUPONS.get(coupon_code)
        if not coupon:
            raise HTTPException(400, detail="Invalid or expired coupon code")

    for item in payload.items:
        product = db.get(m.Product, item.product_id)
        if not product:
            raise HTTPException(400, detail=f"Product {item.product_id} not found")
        if product.quantity < item.quantity:
            raise HTTPException(400, detail=f"Insufficient stock for {product.name}")

        item_total = (item.unit_price * item.quantity) - item.discount
        subtotal += item_total
        tax += item_total * float(product.tax_rate) / 100

    # Apply coupon discount on subtotal (after item discounts)
    if coupon_code and coupon is not None:
        coupon_type = str(coupon["type"])
        coupon_value = float(coupon["value"])  # type: ignore[arg-type]
        if coupon_type == "percent":
            coupon_discount = round(subtotal * (coupon_value / 100), 2)
            max_off = coupon.get("max_off")
            if max_off is not None:
                coupon_discount = min(coupon_discount, float(max_off))  # type: ignore[arg-type]
        else:
            coupon_discount = coupon_value

    order_discount = payload.discount or 0
    total_discount = order_discount + coupon_discount

    total = subtotal + tax - total_discount
    if total < 0:
        total = 0

    # Create sale
    # Persist coupon reference in notes for later visibility
    notes_text = (payload.notes or "").strip()
    if coupon_code:
        notes_suffix = f"Coupon:{coupon_code}"
        notes_text = f"{notes_text} {notes_suffix}".strip()

    sale = m.Sale(
        user_id=user.id,
        customer_id=payload.customer_id,
        subtotal=subtotal,
        tax=tax,
        discount=total_discount,
        coupon_code=coupon_code,
        total=total,
        payment_method=payload.payment_method,
        payment_reference=payload.payment_reference,
        status="completed",
        notes=notes_text or None,
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

    # Award loyalty points: 10 points per $1 spent
    if sale.customer_id:
        customer = db.get(m.Customer, sale.customer_id)
        if customer:
            points_earned = int(float(sale.total) * 10)
            customer.loyalty_points = (customer.loyalty_points or 0) + points_earned
            db.commit()
            db.refresh(customer)

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
        order_discount=float(getattr(sale, "order_discount", 0) or 0),
        coupon_discount=float(getattr(sale, "coupon_discount", 0) or 0),
        coupon_code=getattr(sale, "coupon_code", None),
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
        order_discount=float(getattr(sale, "order_discount", 0) or 0),
        coupon_discount=float(getattr(sale, "coupon_discount", 0) or 0),
        coupon_code=getattr(sale, "coupon_code", None),
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
        order_discount=float(sale.discount),
        coupon_discount=0,
        coupon_code=sale.coupon_code,
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
