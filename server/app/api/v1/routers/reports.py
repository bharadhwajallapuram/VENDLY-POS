"""
Vendly POS - Reports Router with End-of-Day (Z-Reports)
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.error_constants import ErrorCodes, ErrorMessages
from app.core.errors import NotFoundError
from app.db import models as m

router = APIRouter()


# =====================================
# Z-Report & EOD Models
# =====================================


class CashDrawerReconciliation(BaseModel):
    """Cash drawer reconciliation data"""

    expected_cash: float
    actual_cash: float
    variance: float
    variance_percentage: float
    notes: Optional[str] = None


class PaymentMethodBreakdown(BaseModel):
    """Payment method breakdown"""

    method: str
    count: int
    revenue: float
    percentage: float


class ZReportData(BaseModel):
    """End-of-day Z-Report data"""

    report_date: str
    report_time: str

    # Sales summary
    total_sales: int
    total_revenue: float
    total_tax: float
    total_discount: float

    # Items
    items_sold: int

    # Refunds & Returns
    total_refunds: int
    total_returns: int
    refund_amount: float
    return_amount: float

    # Payment breakdown
    payment_methods: List[PaymentMethodBreakdown]

    # Top products
    top_products: list

    # Cash reconciliation (optional)
    cash_reconciliation: Optional[CashDrawerReconciliation] = None

    # Shift info
    shift_start_time: Optional[str] = None
    shift_end_time: Optional[str] = None
    employee_count: Optional[int] = None


class CashReconciliationIn(BaseModel):
    """Cash reconciliation input"""

    actual_cash: float
    notes: Optional[str] = None


@router.get("/summary")
def get_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get sales summary report for a date range"""
    q = db.query(m.Sale).filter(m.Sale.status == "completed")

    if start_date:
        q = q.filter(m.Sale.created_at >= start_date)
    if end_date:
        q = q.filter(m.Sale.created_at <= end_date + " 23:59:59")

    sales = q.all()

    total_sales = len(sales)
    total_revenue = sum(float(s.total) for s in sales)
    total_tax = sum(float(s.tax) for s in sales)
    total_discount = sum(float(s.discount) for s in sales)

    # Get items sold count
    items_sold = 0
    for sale in sales:
        items_sold += sum(item.quantity for item in sale.items)

    # Top products
    product_sales: dict[int, dict[str, int | float | str]] = {}
    for sale in sales:
        for item in sale.items:
            if item.product_id not in product_sales:
                product = db.get(m.Product, item.product_id)
                product_sales[item.product_id] = {
                    "id": item.product_id,
                    "name": product.name if product else "Unknown",
                    "quantity": 0,
                    "revenue": 0.0,
                }
            product_sales[item.product_id]["quantity"] = (
                int(product_sales[item.product_id]["quantity"]) + item.quantity
            )
            product_sales[item.product_id]["revenue"] = float(
                product_sales[item.product_id]["revenue"]
            ) + float(item.subtotal)

    top_products = sorted(
        product_sales.values(), key=lambda x: float(x["revenue"]), reverse=True
    )[:10]

    # Get refund/return statistics
    refund_q = db.query(m.Sale).filter(
        m.Sale.status.in_(
            ["refunded", "partially_refunded", "returned", "partially_returned"]
        )
    )
    if start_date:
        refund_q = refund_q.filter(m.Sale.created_at >= start_date)
    if end_date:
        refund_q = refund_q.filter(m.Sale.created_at <= end_date + " 23:59:59")

    refund_sales = refund_q.all()
    total_refunds = len(
        [s for s in refund_sales if s.status in ("refunded", "partially_refunded")]
    )
    total_returns = len(
        [s for s in refund_sales if s.status in ("returned", "partially_returned")]
    )

    # Calculate refund amounts (rough estimate based on status changes)
    refund_amount = 0.0
    return_amount = 0.0
    for sale in refund_sales:
        if sale.status in ("refunded", "partially_refunded"):
            # For fully refunded, count original total; for partial, estimate half
            if sale.status == "refunded":
                refund_amount += float(sale.total)
            else:
                refund_amount += float(sale.total) * 0.5  # Rough estimate
        elif sale.status in ("returned", "partially_returned"):
            if sale.status == "returned":
                return_amount += float(sale.total)
            else:
                return_amount += float(sale.total) * 0.5

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_tax": total_tax,
        "total_discount": total_discount,
        "items_sold": items_sold,
        "average_sale": total_revenue / total_sales if total_sales > 0 else 0,
        "top_products": top_products,
        # Refund/Return statistics
        "total_refunds": total_refunds,
        "total_returns": total_returns,
        "refund_amount": round(refund_amount, 2),
        "return_amount": round(return_amount, 2),
    }


@router.get("/sales-by-day")
def get_sales_by_day(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get daily sales breakdown"""
    q = db.query(m.Sale).filter(m.Sale.status == "completed")

    if start_date:
        q = q.filter(m.Sale.created_at >= start_date)
    if end_date:
        q = q.filter(m.Sale.created_at <= end_date + " 23:59:59")

    sales = q.order_by(m.Sale.created_at).all()

    # Group by day
    daily_sales: dict[str, dict[str, str | int | float]] = {}
    for sale in sales:
        day = sale.created_at.strftime("%Y-%m-%d")
        if day not in daily_sales:
            daily_sales[day] = {"date": day, "count": 0, "revenue": 0.0}
        daily_sales[day]["count"] = int(daily_sales[day]["count"]) + 1
        daily_sales[day]["revenue"] = float(daily_sales[day]["revenue"]) + float(
            sale.total
        )

    return {"data": list(daily_sales.values())}


@router.get("/sales-by-payment")
def get_sales_by_payment(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get sales breakdown by payment method"""
    q = db.query(m.Sale).filter(m.Sale.status == "completed")

    if start_date:
        q = q.filter(m.Sale.created_at >= start_date)
    if end_date:
        q = q.filter(m.Sale.created_at <= end_date + " 23:59:59")

    sales = q.all()

    # Group by payment method
    by_method: dict[str, dict[str, str | int | float]] = {}
    for sale in sales:
        method = sale.payment_method
        if method not in by_method:
            by_method[method] = {"method": method, "count": 0, "revenue": 0.0}
        by_method[method]["count"] = int(by_method[method]["count"]) + 1
        by_method[method]["revenue"] = float(by_method[method]["revenue"]) + float(
            sale.total
        )

    return {"data": list(by_method.values())}


# =====================================
# Z-Report (End-of-Day) Endpoints
# =====================================


@router.get("/z-report", response_model=ZReportData)
def get_z_report(
    report_date: Optional[str] = Query(None),  # YYYY-MM-DD format
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get end-of-day Z-Report for a specific date.
    Includes sales summary, payment breakdown, refunds/returns, and cash reconciliation.
    """
    # Default to today if no date provided
    if not report_date:
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Parse report date properly
    # When comparing stored UTC times with local date, we need to handle timezone offset
    # Assuming UTC+0 for now, but the key is comparing just the date part
    report_dt = datetime.strptime(report_date, "%Y-%m-%d")

    # Get all completed sales and filter by date using string comparison
    # This works better with SQLite's datetime handling
    sales_q = db.query(m.Sale).filter(m.Sale.status == "completed")
    sales_list = sales_q.all()

    # Filter sales by date (handles timezone properly by comparing date portion only)
    sales = [s for s in sales_list if s.created_at.strftime("%Y-%m-%d") == report_date]

    # Basic metrics
    total_sales = len(sales)
    total_revenue = sum(float(s.total) for s in sales) if sales else 0.0
    total_tax = sum(float(s.tax) for s in sales) if sales else 0.0
    total_discount = sum(float(s.discount) for s in sales) if sales else 0.0

    # Items sold count
    items_sold = sum(sum(item.quantity for item in sale.items) for sale in sales)

    # Payment method breakdown
    payment_methods_dict = {}
    for sale in sales:
        method = sale.payment_method or "unknown"
        if method not in payment_methods_dict:
            payment_methods_dict[method] = {"count": 0, "revenue": 0.0}
        payment_methods_dict[method]["count"] += 1
        payment_methods_dict[method]["revenue"] += float(sale.total)

    # Calculate percentages
    payment_methods = []
    for method, data in payment_methods_dict.items():
        percentage = (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        payment_methods.append(
            PaymentMethodBreakdown(
                method=method,
                count=data["count"],
                revenue=round(data["revenue"], 2),
                percentage=round(percentage, 2),
            )
        )

    # Top products
    product_sales = {}
    for sale in sales:
        for item in sale.items:
            if item.product_id not in product_sales:
                product = db.get(m.Product, item.product_id)
                product_sales[item.product_id] = {
                    "name": product.name if product else "Unknown",
                    "quantity": 0,
                    "revenue": 0.0,
                }
            product_sales[item.product_id]["quantity"] += item.quantity
            product_sales[item.product_id]["revenue"] += float(item.subtotal)

    top_products = sorted(
        [
            {
                "name": p["name"],
                "quantity": p["quantity"],
                "revenue": round(p["revenue"], 2),
            }
            for p in product_sales.values()
        ],
        key=lambda x: x["revenue"],
        reverse=True,
    )[:10]

    # Refunds and returns for the day
    all_refund_sales = (
        db.query(m.Sale)
        .filter(
            m.Sale.status.in_(
                ["refunded", "partially_refunded", "returned", "partially_returned"]
            )
        )
        .all()
    )
    refund_sales = [
        s for s in all_refund_sales if s.created_at.strftime("%Y-%m-%d") == report_date
    ]

    total_refunds = len(
        [s for s in refund_sales if s.status in ("refunded", "partially_refunded")]
    )
    total_returns = len(
        [s for s in refund_sales if s.status in ("returned", "partially_returned")]
    )

    refund_amount = 0.0
    return_amount = 0.0
    for sale in refund_sales:
        if sale.status in ("refunded", "partially_refunded"):
            refund_amount += (
                float(sale.total)
                if sale.status == "refunded"
                else float(sale.total) * 0.5
            )
        elif sale.status in ("returned", "partially_returned"):
            return_amount += (
                float(sale.total)
                if sale.status == "returned"
                else float(sale.total) * 0.5
            )

    # Report timing
    now = datetime.now()
    report_time = now.strftime("%H:%M:%S")

    return ZReportData(
        report_date=report_date,
        report_time=report_time,
        total_sales=total_sales,
        total_revenue=round(total_revenue, 2),
        total_tax=round(total_tax, 2),
        total_discount=round(total_discount, 2),
        items_sold=items_sold,
        total_refunds=total_refunds,
        total_returns=total_returns,
        refund_amount=round(refund_amount, 2),
        return_amount=round(return_amount, 2),
        payment_methods=payment_methods,
        top_products=top_products,
        shift_start_time="06:00:00",  # Can be configurable
        shift_end_time=report_time,
        employee_count=db.query(m.User).count(),
    )


@router.post("/z-report/reconcile")
def reconcile_cash_drawer(
    report_date: Optional[str] = Query(None),
    reconciliation: CashReconciliationIn = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Reconcile cash drawer for end-of-day.
    Compares expected cash (from sales) with actual cash counted.
    """
    if not report_date:
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get all cash sales and filter by date
    all_cash_sales = (
        db.query(m.Sale)
        .filter(m.Sale.status == "completed", m.Sale.payment_method == "cash")
        .all()
    )

    cash_sales = [
        s for s in all_cash_sales if s.created_at.strftime("%Y-%m-%d") == report_date
    ]

    # Calculate expected cash
    expected_cash = sum(float(s.total) for s in cash_sales) if cash_sales else 0.0

    # Get actual cash from reconciliation
    actual_cash = reconciliation.actual_cash if reconciliation else 0.0

    # Calculate variance
    variance = actual_cash - expected_cash
    variance_percentage = (variance / expected_cash * 100) if expected_cash > 0 else 0

    # Create reconciliation record
    reconciliation_data = CashDrawerReconciliation(
        expected_cash=round(expected_cash, 2),
        actual_cash=round(actual_cash, 2),
        variance=round(variance, 2),
        variance_percentage=round(variance_percentage, 2),
        notes=reconciliation.notes if reconciliation else None,
    )

    return {
        "report_date": report_date,
        "reconciliation": reconciliation_data,
        "status": "success" if abs(variance) < 1.0 else "variance_detected",
        "message": (
            "Cash drawer reconciled successfully"
            if abs(variance) < 1.0
            else f"Variance of ${abs(variance):.2f} detected"
        ),
    }


@router.get("/sales-summary")
def get_sales_summary(
    report_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get daily sales summary without cash reconciliation details"""
    if not report_date:
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get all completed sales and filter by date
    all_sales = db.query(m.Sale).filter(m.Sale.status == "completed").all()

    sales = [s for s in all_sales if s.created_at.strftime("%Y-%m-%d") == report_date]

    total_sales = len(sales)
    total_revenue = sum(float(s.total) for s in sales) if sales else 0.0
    total_tax = sum(float(s.tax) for s in sales) if sales else 0.0
    total_discount = sum(float(s.discount) for s in sales) if sales else 0.0

    items_sold = sum(sum(item.quantity for item in sale.items) for sale in sales)

    return {
        "date": report_date,
        "total_sales": total_sales,
        "total_revenue": round(total_revenue, 2),
        "total_tax": round(total_tax, 2),
        "total_discount": round(total_discount, 2),
        "items_sold": items_sold,
        "average_transaction": (
            round(total_revenue / total_sales, 2) if total_sales > 0 else 0
        ),
    }
