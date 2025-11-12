from sqlalchemy.orm import Session

from app.db import models as m


def recalc_totals(sale: m.Sale) -> None:
    subtotal = 0
    for ln in sale.lines:
        ln.line_total_cents = (
            ln.qty * ln.unit_price_cents - ln.discount_cents + ln.tax_cents
        )
        subtotal += ln.line_total_cents
    sale.subtotal_cents = subtotal
    sale.total_cents = sale.subtotal_cents - sale.discount_cents + sale.tax_cents


def get_or_create_payment_method(db: Session, code: str) -> m.PaymentMethod:
    pm = db.query(m.PaymentMethod).filter(m.PaymentMethod.code == code).first()
    if not pm:
        pm = m.PaymentMethod(code=code, name=code.capitalize())
        db.add(pm)
        db.commit()
        db.refresh(pm)
    return pm
