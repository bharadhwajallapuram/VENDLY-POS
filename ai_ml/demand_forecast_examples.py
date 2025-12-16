#!/usr/bin/env python3
# ===========================================
# Vendly POS - Demand Forecasting Integration Examples
# Usage: python demand_forecast_examples.py
# ===========================================

"""
Practical examples for using the demand forecasting system.
Run examples individually or as a complete workflow.
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from server.app.db.session import SessionLocal, engine
from server.app.db import models as m
from server.app.services.demand_forecast_service import DemandForecastService


def setup_demo_data(db: Session):
    """Create sample products and sales history for demo"""
    print("\n📦 Setting up demo data...")
    
    # Create demo category
    category = db.query(m.Category).filter(
        m.Category.name == "Demo Products"
    ).first()
    
    if not category:
        category = m.Category(
            name="Demo Products",
            description="Demo products for forecasting examples"
        )
        db.add(category)
        db.flush()
    
    # Create demo products
    demo_products = [
        {
            "name": "Organic Coffee Beans",
            "sku": "COFFEE-001",
            "barcode": "1234567001",
            "price": 12.99,
            "cost": 5.00,
            "category_id": category.id,
        },
        {
            "name": "Premium Green Tea",
            "sku": "TEA-001",
            "barcode": "1234567002",
            "price": 8.99,
            "cost": 3.00,
            "category_id": category.id,
        },
        {
            "name": "Natural Honey",
            "sku": "HONEY-001",
            "barcode": "1234567003",
            "price": 15.99,
            "cost": 7.00,
            "category_id": category.id,
        },
    ]
    
    products = []
    for prod_data in demo_products:
        product = db.query(m.Product).filter(
            m.Product.sku == prod_data["sku"]
        ).first()
        
        if not product:
            product = m.Product(**prod_data)
            db.add(product)
            db.flush()
            print(f"  ✓ Created: {product.name}")
        
        products.append(product)
    
    # Create 90 days of sales history
    print("\n  Creating 90 days of sales history...")
    base_date = datetime.utcnow() - timedelta(days=90)
    
    for product in products:
        for i in range(90):
            date = base_date + timedelta(days=i)
            
            # Simulate realistic sales patterns
            base_qty = 10
            if product.name == "Organic Coffee Beans":
                # Coffee: weekday high, weekend low
                qty = base_qty + (5 if date.weekday() < 5 else -2)
            elif product.name == "Premium Green Tea":
                # Tea: increasing trend
                qty = base_qty + int(i * 0.1)
            else:
                # Honey: stable with seasonal spike
                qty = base_qty + (3 if date.month in [6, 7, 8] else 0)
            
            qty += np.random.randint(-2, 3)  # Random noise
            qty = max(2, qty)  # Minimum 2 units
            
            history = m.DemandHistory(
                product_id=product.id,
                date=date,
                quantity_sold=int(qty),
                revenue=float(qty * product.price),
                day_of_week=date.weekday(),
                is_weekend=date.weekday() >= 5,
            )
            db.add(history)
    
    db.commit()
    print(f"  ✓ Created sales history for {len(products)} products")
    
    return products


def example_1_basic_forecast(db: Session, service: DemandForecastService):
    """Example 1: Generate a basic forecast"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Generate a Basic Forecast")
    print("=" * 70)
    
    # Get a product
    product = db.query(m.Product).filter(
        m.Product.sku == "COFFEE-001"
    ).first()
    
    if not product:
        print("✗ Product not found")
        return
    
    print(f"\n📊 Generating 30-day forecast for: {product.name}")
    
    # Generate forecast
    forecast = service.generate_forecast(
        db=db,
        product_id=product.id,
        days_ahead=30,
        model_type='ensemble'
    )
    
    if "error" in forecast:
        print(f"✗ Error: {forecast['error']}")
        return
    
    print(f"\n✓ Forecast Generated!")
    print(f"  ID: {forecast['forecast_id']}")
    print(f"  Average daily demand: {forecast['average_demand']:.1f} units")
    print(f"  Forecast horizon: {forecast['forecast_horizon']} days")
    
    # Show first week
    print(f"\n  First 7 days:")
    for i, day in enumerate(forecast['forecast'][:7], 1):
        print(f"    Day {i} ({day['date']}): {day['forecast']:.0f} units "
              f"(±{(day['upper_bound']-day['lower_bound'])/2:.0f})")
    
    return forecast['forecast_id']


def example_2_forecast_summary(db: Session, service: DemandForecastService):
    """Example 2: Get forecast summary and next 7 days"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Forecast Summary & Next 7 Days")
    print("=" * 70)
    
    product = db.query(m.Product).filter(
        m.Product.sku == "TEA-001"
    ).first()
    
    if not product:
        print("✗ Product not found")
        return
    
    print(f"\n📋 Getting summary for: {product.name}")
    
    # Generate forecast
    service.generate_forecast(db, product.id, days_ahead=14)
    
    # Get summary
    summary = service.get_forecast_summary(db, product.id)
    
    if "error" in summary:
        print(f"✗ Error: {summary['error']}")
        return
    
    print(f"\n✓ Forecast Summary:")
    print(f"  Current stock: {summary['current_stock']} units")
    print(f"  Model type: {summary['model_type']}")
    print(f"  Average demand: {summary['average_demand']:.1f} units/day")
    
    if summary.get('mae'):
        print(f"  Forecast accuracy (R²): {summary['r2_score']:.2%}")
    
    print(f"\n  Next 7 Days Forecast:")
    for day in summary['next_7_days']:
        print(f"    {day['date']}: {day['forecast']:.0f} units "
              f"[{day['lower_bound']:.0f}-{day['upper_bound']:.0f}]")


def example_3_low_stock_alerts(db: Session, service: DemandForecastService):
    """Example 3: Check for low stock alerts"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Low Stock Alerts")
    print("=" * 70)
    
    print(f"\n⚠️  Checking for products with low stock in next 7 days...")
    
    # Generate forecasts for all products first
    products = db.query(m.Product).filter(
        m.Product.sku.in_(["COFFEE-001", "TEA-001", "HONEY-001"])
    ).all()
    
    for product in products:
        service.generate_forecast(db, product.id, days_ahead=14)
    
    # Get low stock alerts
    alerts = service.get_low_stock_alerts(db, threshold_days=7)
    
    if not alerts:
        print("\n✓ All products have sufficient stock!")
        return
    
    print(f"\n✗ Found {len(alerts)} low stock alerts:\n")
    
    for alert in alerts:
        print(f"  📦 {alert['product_name']}")
        print(f"     Current stock: {alert['current_stock']} units")
        print(f"     7-day forecast: {alert['forecasted_demand']:.0f} units")
        print(f"     Shortage: {alert['shortage']:.0f} units")
        print(f"     → Recommended reorder: {alert['reorder_quantity']} units\n")


def example_4_forecast_comparison(db: Session, service: DemandForecastService):
    """Example 4: Compare forecast vs actual sales"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Forecast vs Actual Comparison")
    print("=" * 70)
    
    product = db.query(m.Product).filter(
        m.Product.sku == "HONEY-001"
    ).first()
    
    if not product:
        print("✗ Product not found")
        return
    
    print(f"\n📈 Comparing forecast vs actual for: {product.name}")
    
    # Generate forecast
    forecast = service.generate_forecast(db, product.id, days_ahead=14)
    
    # Get comparison
    comparison = service.get_product_forecast_comparison(db, product.id, days=14)
    
    if "error" in comparison:
        print(f"✗ Error: {comparison['error']}")
        return
    
    print(f"\n✓ Forecast Comparison (first 7 days):")
    print(f"  Average accuracy: {comparison['avg_accuracy']:.1f}%\n")
    
    print(f"  {'Date':<12} {'Forecast':<12} {'Actual':<12} {'Error':<12} {'Accuracy':<12}")
    print(f"  " + "-" * 60)
    
    for item in comparison['comparison'][:7]:
        print(f"  {item['date']:<12} "
              f"{item['forecasted']:<12.0f} "
              f"{item['actual']:<12.0f} "
              f"{item['error']:<12.0f} "
              f"{item['accuracy_percent']:<12.0f}%")


def example_5_evaluate_forecast(db: Session, service: DemandForecastService, forecast_id: int = None):
    """Example 5: Evaluate forecast accuracy"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Evaluate Forecast Accuracy")
    print("=" * 70)
    
    # Get latest forecast if not specified
    if not forecast_id:
        forecast = db.query(m.DemandForecast).order_by(
            m.DemandForecast.created_at.desc()
        ).first()
        if forecast:
            forecast_id = forecast.id
    
    if not forecast_id:
        print("✗ No forecasts found")
        return
    
    print(f"\n📊 Evaluating forecast {forecast_id}...")
    
    # Evaluate
    evaluation = service.evaluate_forecast(db, forecast_id)
    
    if "error" in evaluation:
        print(f"✗ Error: {evaluation['error']}")
        return
    
    metrics = evaluation['metrics']
    
    print(f"\n✓ Evaluation Results:")
    print(f"  Mean Absolute Error (MAE): {metrics['mae']:.2f} units")
    print(f"  Mean Absolute % Error (MAPE): {metrics['mape']:.1f}%" if metrics.get('mape') else "")
    print(f"  Root Mean Squared Error (RMSE): {metrics['rmse']:.2f} units")
    print(f"  R² Score: {metrics['r2']:.3f}")
    print(f"  Samples evaluated: {metrics['samples']}")
    
    # Interpretation
    print(f"\n  Interpretation:")
    if metrics['r2'] > 0.85:
        print(f"    ✓ Excellent forecast accuracy")
    elif metrics['r2'] > 0.70:
        print(f"    ○ Good forecast accuracy")
    elif metrics['r2'] > 0.50:
        print(f"    △ Fair forecast accuracy")
    else:
        print(f"    ✗ Poor forecast accuracy - consider more data or model adjustment")


def example_6_full_workflow(db: Session, service: DemandForecastService):
    """Example 6: Complete forecasting workflow"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete Forecasting Workflow")
    print("=" * 70)
    
    # Get all demo products
    products = db.query(m.Product).filter(
        m.Product.sku.in_(["COFFEE-001", "TEA-001", "HONEY-001"])
    ).all()
    
    print(f"\n🔄 Running complete workflow for {len(products)} products:\n")
    
    for product in products:
        print(f"Processing: {product.name}")
        print("-" * 50)
        
        # 1. Generate forecast
        forecast = service.generate_forecast(db, product.id, days_ahead=30)
        if "error" in forecast:
            print(f"  ✗ Failed: {forecast['error']}\n")
            continue
        
        print(f"  ✓ Generated 30-day forecast (ID: {forecast['forecast_id']})")
        
        # 2. Get summary
        summary = service.get_forecast_summary(db, product.id)
        print(f"  ✓ Average demand: {summary['average_demand']:.1f} units/day")
        print(f"  ✓ Current stock: {summary['current_stock']} units")
        
        # 3. Check if low stock
        alerts = service.get_low_stock_alerts(db, threshold_days=7)
        low_stock = [a for a in alerts if a['product_id'] == product.id]
        
        if low_stock:
            alert = low_stock[0]
            print(f"  ⚠️  Low stock alert: Reorder {alert['reorder_quantity']} units")
        else:
            print(f"  ✓ Stock level is good")
        
        # 4. Get accuracy metrics
        if summary.get('r2_score'):
            print(f"  ✓ Forecast accuracy (R²): {summary['r2_score']:.2%}")
        
        print()


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("🎯 VENDLY DEMAND FORECASTING EXAMPLES")
    print("=" * 70)
    
    # Initialize database session
    db = SessionLocal()
    service = DemandForecastService()
    
    try:
        # Create demo data
        setup_demo_data(db)
        
        # Run examples
        forecast_id = example_1_basic_forecast(db, service)
        example_2_forecast_summary(db, service)
        example_3_low_stock_alerts(db, service)
        example_4_forecast_comparison(db, service)
        
        if forecast_id:
            example_5_evaluate_forecast(db, service, forecast_id)
        
        example_6_full_workflow(db, service)
        
        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70)
        print("\n📚 For more information, see: ai_ml/DEMAND_FORECASTING.md")
        print("🚀 Quick start guide: ai_ml/QUICKSTART_DEMAND_FORECASTING.md\n")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
