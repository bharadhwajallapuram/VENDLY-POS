"""
Vendly POS - Sales Service
===========================
Business logic for sales operations
"""

from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db import models as m

# Accepted payment methods
VALID_PAYMENT_METHODS = [
    "cash",
    "card",
    "upi",
    "credit_card",
    "debit_card",
    "stripe",
    "paypal",
    "bank_transfer",
    "store_credit",
    "split",
    "other",
]


def recalc_totals(
    db: Session,
    sale: m.Sale,
    items: Optional[List[m.SaleItem]] = None,
) -> Tuple[float, float, float]:
    """
    Recalculate sale totals based on items.

    Args:
        db: Database session
        sale: The sale to recalculate
        items: Optional list of sale items (uses sale.items if not provided)

    Returns:
        Tuple of (subtotal, tax, total)
    """
    if items is None:
        items = sale.items or []

    subtotal = Decimal("0.00")
    tax = Decimal("0.00")

    for item in items:
        # Get product for tax rate
        product = db.get(m.Product, item.product_id)
        tax_rate = Decimal(str(product.tax_rate)) if product else Decimal("0.00")

        # Calculate item subtotal (unit_price * quantity - discount)
        item_subtotal = (Decimal(str(item.unit_price)) * item.quantity) - Decimal(
            str(item.discount or 0)
        )
        subtotal += item_subtotal

        # Calculate tax for this item
        item_tax = item_subtotal * (tax_rate / Decimal("100"))
        tax += item_tax

    # Apply discounts
    order_discount = Decimal(str(getattr(sale, "order_discount", 0) or 0))
    coupon_discount = Decimal(str(getattr(sale, "coupon_discount", 0) or 0))
    total_discount = order_discount + coupon_discount

    # Calculate total
    total = subtotal + tax - total_discount
    if total < 0:
        total = Decimal("0.00")

    # Update sale record
    sale.subtotal = float(subtotal)
    sale.tax = float(tax)
    sale.discount = float(total_discount)
    sale.total = float(total)

    return float(subtotal), float(tax), float(total)


def get_or_create_payment_method(
    payment_method: str,
    validate_only: bool = False,
) -> str:
    """
    Validate and normalize payment method string.

    Args:
        payment_method: The payment method to validate
        validate_only: If True, raises ValueError for invalid methods

    Returns:
        Normalized payment method string (lowercase)

    Raises:
        ValueError: If validate_only is True and method is invalid
    """
    if not payment_method:
        return "cash"

    normalized = payment_method.strip().lower()

    # Check if it's a valid method
    if normalized in VALID_PAYMENT_METHODS:
        return normalized

    # If validation is strict, raise error
    if validate_only:
        raise ValueError(
            f"Invalid payment method: {payment_method}. "
            f"Valid methods: {', '.join(VALID_PAYMENT_METHODS)}"
        )

    # Default to 'other' for unknown methods
    return "other"


def calculate_item_totals(
    unit_price: float,
    quantity: int,
    discount: float = 0.0,
    tax_rate: float = 0.0,
) -> dict:
    """
    Calculate totals for a single sale item.

    Args:
        unit_price: Price per unit
        quantity: Number of units
        discount: Discount amount (not percentage)
        tax_rate: Tax rate as percentage (e.g., 10 for 10%)

    Returns:
        Dictionary with subtotal, tax, and total
    """
    subtotal = (Decimal(str(unit_price)) * quantity) - Decimal(str(discount))
    tax = subtotal * (Decimal(str(tax_rate)) / Decimal("100"))
    total = subtotal + tax

    return {
        "subtotal": float(subtotal),
        "tax": float(tax),
        "total": float(total),
    }


def validate_sale_items(
    db: Session,
    items: list,
    check_stock: bool = True,
) -> List[str]:
    """
    Validate sale items before creating a sale.

    Args:
        db: Database session
        items: List of items with product_id and quantity
        check_stock: Whether to check stock availability

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    for item in items:
        product_id = getattr(item, "product_id", None) or item.get("product_id")
        quantity = getattr(item, "quantity", None) or item.get("quantity", 0)

        product = db.get(m.Product, product_id)

        if not product:
            errors.append(f"Product {product_id} not found")
            continue

        if not product.is_active:
            errors.append(f"Product '{product.name}' is not active")
            continue

        if check_stock and product.quantity < quantity:
            errors.append(
                f"Insufficient stock for '{product.name}': "
                f"requested {quantity}, available {product.quantity}"
            )

    return errors
