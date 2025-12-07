"""
Vendly POS - Reports Router
"""
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m

router = APIRouter()


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
    product_sales = {}
    for sale in sales:
        for item in sale.items:
            if item.product_id not in product_sales:
                product = db.get(m.Product, item.product_id)
                product_sales[item.product_id] = {
                    "id": item.product_id,
                    "name": product.name if product else "Unknown",
                    "quantity": 0,
                    "revenue": 0,
                }
            product_sales[item.product_id]["quantity"] += item.quantity
            product_sales[item.product_id]["revenue"] += float(item.total)
    
    top_products = sorted(
        product_sales.values(), key=lambda x: x["revenue"], reverse=True
    )[:10]
    
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
    daily_sales = {}
    for sale in sales:
        day = sale.created_at.strftime("%Y-%m-%d")
        if day not in daily_sales:
            daily_sales[day] = {"date": day, "count": 0, "revenue": 0}
        daily_sales[day]["count"] += 1
        daily_sales[day]["revenue"] += float(sale.total)
    
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
    by_method = {}
    for sale in sales:
        method = sale.payment_method
        if method not in by_method:
            by_method[method] = {"method": method, "count": 0, "revenue": 0}
        by_method[method]["count"] += 1
        by_method[method]["revenue"] += float(sale.total)
    
    return {"data": list(by_method.values())}
