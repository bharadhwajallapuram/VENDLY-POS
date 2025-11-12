from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.db import models as m
from app.api.v1.schemas.sales import SaleOpenIn, SaleOut, SaleLineIn, PaymentIn, CompleteOut
from app.services.sales import recalc_totals, get_or_create_payment_method
from app.services.ws_manager import manager

router = APIRouter()

@router.post("", response_model=SaleOut, status_code=201)
def open_sale(payload: SaleOpenIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # For demo: use a placeholder UUID since we don't have real user records
    demo_user_id = uuid4()  # Generate a demo UUID for the user
    sale = m.Sale(store_id=payload.store_id, register_id=payload.register_id, user_id=demo_user_id)
    db.add(sale)
    db.commit(); db.refresh(sale)
    return SaleOut(id=sale.id, status=sale.status, subtotal_cents=sale.subtotal_cents, discount_cents=sale.discount_cents, tax_cents=sale.tax_cents, total_cents=sale.total_cents)

@router.post("/{sale_id}/lines", response_model=SaleOut)
def add_line(sale_id: UUID, payload: SaleLineIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sale = db.get(m.Sale, sale_id); 
    if not sale or sale.status != "open": raise HTTPException(400, detail="Sale not open")
    line = m.SaleLine(sale_id=sale.id, variant_id=payload.variant_id, qty=payload.qty, unit_price_cents=payload.unit_price_cents)
    sale.lines.append(line)
    recalc_totals(sale)
    db.commit(); db.refresh(sale)
    return SaleOut(id=sale.id, status=sale.status, subtotal_cents=sale.subtotal_cents, discount_cents=sale.discount_cents, tax_cents=sale.tax_cents, total_cents=sale.total_cents)

@router.post("/{sale_id}/payments", response_model=SaleOut)
def add_payment(sale_id: UUID, payload: PaymentIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sale = db.get(m.Sale, sale_id)
    if not sale or sale.status != "open": raise HTTPException(400, detail="Sale not open")
    pm = get_or_create_payment_method(db, payload.method_code)
    sale.payments.append(m.Payment(sale_id=sale.id, method_id=pm.id, amount_cents=payload.amount_cents))
    recalc_totals(sale)
    db.commit(); db.refresh(sale)
    return SaleOut(id=sale.id, status=sale.status, subtotal_cents=sale.subtotal_cents, discount_cents=sale.discount_cents, tax_cents=sale.tax_cents, total_cents=sale.total_cents)

@router.post("/{sale_id}/complete", response_model=CompleteOut)
def complete_sale(sale_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sale = db.get(m.Sale, sale_id)
    if not sale or sale.status != "open": raise HTTPException(400, detail="Sale not open")
    sale.status = "completed"; sale.completed_at = datetime.utcnow()
    db.commit(); db.refresh(sale)
    # broadcast
    try:
        import anyio
        anyio.from_thread.run(manager.broadcast, {"event": "sale.completed", "sale_id": str(sale.id), "total_cents": sale.total_cents})
    except Exception:
        pass
    return CompleteOut(id=sale.id, total_cents=sale.total_cents, status=sale.status)