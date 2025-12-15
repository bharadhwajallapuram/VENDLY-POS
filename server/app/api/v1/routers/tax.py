# ===========================================
# Tax Configuration & Management API
# ===========================================

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.services.tax_service import TaxService

router = APIRouter(prefix="/tax", tags=["tax"])


# ==================== Schemas ====================


class TaxRateCreate(BaseModel):
    region: str
    tax_type: str
    name: str
    rate: float
    state_code: Optional[str] = None
    description: Optional[str] = None


class TaxRateOut(BaseModel):
    id: int
    region: str
    tax_type: str
    name: str
    rate: float
    state_code: Optional[str]
    is_active: bool
    effective_from: datetime
    effective_to: Optional[datetime]
    description: Optional[str]

    class Config:
        from_attributes = True


class TaxConfigurationOut(BaseModel):
    id: int
    region: str
    tax_id: Optional[str]
    is_tax_exempt: bool
    enable_compound_tax: bool
    enable_reverse_charge: bool
    enable_tax_invoice: bool
    rounding_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaxConfigUpdate(BaseModel):
    tax_id: Optional[str] = None
    is_tax_exempt: Optional[bool] = None
    enable_compound_tax: Optional[bool] = None
    enable_reverse_charge: Optional[bool] = None
    enable_tax_invoice: Optional[bool] = None
    rounding_method: Optional[str] = None


class TaxCalculationResult(BaseModel):
    tax_amount: float
    tax_rate: float
    tax_type: str
    taxable_base: float


class CompoundTaxResult(BaseModel):
    total_tax: float
    subtotal: float
    total_with_tax: float
    calculations: List[TaxCalculationResult]


class TaxReportOut(BaseModel):
    region: str
    period: dict
    total_subtotal: float
    total_tax: float
    total_with_tax: float
    by_type: dict


# ==================== Tax Rates ====================


@router.get("/rates", response_model=List[TaxRateOut])
def get_tax_rates(
    region: Optional[str] = Query(None),
    tax_type: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get tax rates with optional filtering"""
    service = TaxService(db)
    rates = service.get_tax_rates(region=region, tax_type=tax_type, is_active=is_active)
    return rates


@router.post("/rates", response_model=TaxRateOut, status_code=201)
def create_tax_rate(
    payload: TaxRateCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new tax rate (admin only)"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can create tax rates")

    service = TaxService(db)
    rate = service.create_tax_rate(
        region=payload.region,
        tax_type=payload.tax_type,
        name=payload.name,
        rate=payload.rate,
        state_code=payload.state_code,
        description=payload.description,
    )
    return rate


@router.get("/rates/{rate_id}", response_model=TaxRateOut)
def get_tax_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a specific tax rate"""
    service = TaxService(db)
    rate = service.get_tax_rate(rate_id)
    if not rate:
        raise HTTPException(404, detail="Tax rate not found")
    return rate


@router.put("/rates/{rate_id}", response_model=TaxRateOut)
def update_tax_rate(
    rate_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a tax rate (admin only)"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can update tax rates")

    service = TaxService(db)
    rate = service.update_tax_rate(
        tax_rate_id=rate_id,
        rate=payload.get("rate"),
        is_active=payload.get("is_active"),
        description=payload.get("description"),
    )
    if not rate:
        raise HTTPException(404, detail="Tax rate not found")
    return rate


# ==================== Tax Configuration ====================


@router.get("/config/{region}", response_model=TaxConfigurationOut)
def get_tax_config(
    region: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get tax configuration for current user's region"""
    service = TaxService(db)
    config = service.get_or_create_config(user_id=user.id, region=region)
    return config


@router.put("/config/{config_id}", response_model=TaxConfigurationOut)
def update_tax_config(
    config_id: int,
    payload: TaxConfigUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update tax configuration"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can update tax configuration")

    service = TaxService(db)
    config = service.update_config(
        config_id=config_id,
        tax_id=payload.tax_id,
        is_tax_exempt=payload.is_tax_exempt,
        enable_compound_tax=payload.enable_compound_tax,
        enable_reverse_charge=payload.enable_reverse_charge,
        enable_tax_invoice=payload.enable_tax_invoice,
        rounding_method=payload.rounding_method,
    )
    if not config:
        raise HTTPException(404, detail="Tax configuration not found")
    return config


# ==================== Tax Calculation ====================


@router.post("/calculate", response_model=TaxCalculationResult)
def calculate_tax(
    subtotal: float = Query(...),
    tax_rate_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Calculate tax for a given subtotal"""
    service = TaxService(db)
    result = service.calculate_tax(subtotal=subtotal, tax_rate_id=tax_rate_id)
    return result


@router.post("/calculate-compound", response_model=CompoundTaxResult)
def calculate_compound_tax(
    subtotal: float = Query(...),
    tax_rate_ids: str = Query(...),  # Comma-separated IDs
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Calculate compound tax (e.g., CGST + SGST)"""
    try:
        rate_ids = [int(x.strip()) for x in tax_rate_ids.split(",")]
    except ValueError:
        raise HTTPException(400, detail="Invalid tax_rate_ids format")

    service = TaxService(db)
    result = service.calculate_compound_tax(subtotal=subtotal, tax_rate_ids=rate_ids)
    return result


# ==================== Tax Reporting ====================


@router.get("/report", response_model=TaxReportOut)
def get_tax_report(
    region: str = Query(...),
    tax_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get tax report for a region"""
    if user.role not in ["admin", "manager"]:
        raise HTTPException(403, detail="Only admins/managers can view tax reports")

    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
    except ValueError:
        raise HTTPException(400, detail="Invalid date format (use ISO format)")

    service = TaxService(db)
    report = service.get_tax_report(
        region=region,
        tax_type=tax_type,
        start_date=start,
        end_date=end,
    )
    return report


@router.get("/report/by-rate")
def get_tax_by_rate(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get tax summary by rate"""
    if user.role not in ["admin", "manager"]:
        raise HTTPException(403, detail="Only admins/managers can view tax reports")

    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
    except ValueError:
        raise HTTPException(400, detail="Invalid date format")

    service = TaxService(db)
    report = service.get_tax_by_rate(start_date=start, end_date=end)
    return report
