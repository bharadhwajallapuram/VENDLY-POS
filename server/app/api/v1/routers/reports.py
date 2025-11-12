from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.db import models as m

router = APIRouter()

@router.get("/sales-summary")
def sales_summary(from_dt: str, to_dt: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # naive window (UTC strings)
    q = db.query(m.Sale).filter(m.Sale.status=="completed")
    if from_dt:
        q = q.filter(m.Sale.completed_at >= from_dt)
    if to_dt:
        q = q.filter(m.Sale.completed_at <= to_dt)
    total = sum(s.total_cents for s in q.all())
    return {"from": from_dt, "to": to_dt, "total_cents": total}