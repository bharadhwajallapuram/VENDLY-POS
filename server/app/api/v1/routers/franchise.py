"""
Vendly POS - Franchise Fee Management API
==========================================
Royalty calculation, fee tracking, franchise reporting
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.subscription_models import Store, Tenant, TenantUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/franchise", tags=["franchise"])


# ============================================
# Schemas
# ============================================


class FeeConfigCreate(BaseModel):
    fee_type: str = Field(
        ..., pattern="^(royalty|marketing|technology|initial|renewal|other)$"
    )
    calculation_type: str = Field(
        "percentage", pattern="^(percentage|fixed|tiered|per_transaction)$"
    )
    rate: float = Field(0.0, ge=0, le=1)  # For percentage (0.05 = 5%)
    fixed_amount: float = Field(0.0, ge=0)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tier_brackets: Optional[List[dict]] = (
        None  # [{"min": 0, "max": 10000, "rate": 0.06}]
    )
    billing_day: int = Field(1, ge=1, le=28)
    effective_from: Optional[datetime] = None


class FeeConfigUpdate(BaseModel):
    rate: Optional[float] = None
    fixed_amount: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tier_brackets: Optional[List[dict]] = None
    billing_day: Optional[int] = None
    is_active: Optional[bool] = None


class FeeConfigResponse(BaseModel):
    id: int
    tenant_id: int
    fee_type: str
    calculation_type: str
    rate: float
    fixed_amount: float
    min_amount: Optional[float]
    max_amount: Optional[float]
    tier_brackets: Optional[List[dict]]
    billing_day: int
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime]

    class Config:
        from_attributes = True


class FeeRecordResponse(BaseModel):
    id: int
    tenant_id: int
    store_id: Optional[int]
    period_start: datetime
    period_end: datetime
    gross_sales: float
    transaction_count: int
    calculated_fee: float
    adjustments: float
    final_fee: float
    status: str
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class FeeCalculationRequest(BaseModel):
    store_id: Optional[int] = None  # None = all stores
    period_start: datetime
    period_end: datetime
    fee_types: List[str] = ["royalty", "marketing"]


class FeeCalculationResult(BaseModel):
    fee_type: str
    gross_sales: float
    transaction_count: int
    rate_applied: float
    calculated_amount: float
    min_applied: bool = False
    max_applied: bool = False
    final_amount: float


class FranchiseSummary(BaseModel):
    tenant_id: int
    tenant_name: str
    period: str
    total_gross_sales: float
    total_fees_due: float
    total_fees_paid: float
    outstanding_balance: float
    stores_count: int
    fee_breakdown: List[dict]


# ============================================
# Helper Functions
# ============================================


def get_user_tenant(db: Session, user_id: int) -> Optional[Tenant]:
    """Get the tenant for a user"""
    tenant_user = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user_id, TenantUser.is_active == True)
        .first()
    )
    if tenant_user:
        return db.query(Tenant).filter(Tenant.id == tenant_user.tenant_id).first()
    return None


def calculate_tiered_fee(gross_sales: float, tier_brackets: List[dict]) -> float:
    """Calculate fee using tiered brackets"""
    total_fee = 0.0
    remaining_sales = gross_sales

    # Sort brackets by min
    sorted_brackets = sorted(tier_brackets, key=lambda x: x.get("min", 0))

    for bracket in sorted_brackets:
        bracket_min = bracket.get("min", 0)
        bracket_max = bracket.get("max", float("inf"))
        rate = bracket.get("rate", 0)

        if remaining_sales <= 0:
            break

        # Amount in this bracket
        bracket_amount = min(remaining_sales, bracket_max - bracket_min)
        if bracket_amount > 0:
            total_fee += bracket_amount * rate
            remaining_sales -= bracket_amount

    return total_fee


def calculate_fee(
    gross_sales: float,
    transaction_count: int,
    calculation_type: str,
    rate: float,
    fixed_amount: float,
    min_amount: Optional[float],
    max_amount: Optional[float],
    tier_brackets: Optional[str],
) -> tuple[float, float, bool, bool]:
    """Calculate fee based on configuration. Returns (calculated, final, min_applied, max_applied)"""
    calculated = 0.0

    if calculation_type == "percentage":
        calculated = gross_sales * rate
    elif calculation_type == "fixed":
        calculated = fixed_amount
    elif calculation_type == "per_transaction":
        calculated = transaction_count * fixed_amount
    elif calculation_type == "tiered" and tier_brackets:
        try:
            brackets = (
                json.loads(tier_brackets)
                if isinstance(tier_brackets, str)
                else tier_brackets
            )
            calculated = calculate_tiered_fee(gross_sales, brackets)
        except (json.JSONDecodeError, TypeError):
            calculated = gross_sales * rate  # Fallback to percentage

    # Apply min/max caps
    final = calculated
    min_applied = False
    max_applied = False

    if min_amount is not None and final < min_amount:
        final = min_amount
        min_applied = True

    if max_amount is not None and final > max_amount:
        final = max_amount
        max_applied = True

    return calculated, final, min_applied, max_applied


# ============================================
# Fee Configuration Endpoints
# ============================================


@router.get("/fees/config", response_model=List[FeeConfigResponse])
def list_fee_configs(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List franchise fee configurations"""
    from app.db.multistore_models import FranchiseFeeConfig

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    query = db.query(FranchiseFeeConfig).filter(
        FranchiseFeeConfig.tenant_id == tenant.id
    )

    if not include_inactive:
        query = query.filter(FranchiseFeeConfig.is_active == True)

    configs = query.all()

    # Parse tier_brackets JSON
    result = []
    for config in configs:
        result.append(
            FeeConfigResponse(
                id=int(config.id),
                tenant_id=int(config.tenant_id),
                fee_type=str(config.fee_type),
                calculation_type=str(config.calculation_type),
                rate=float(config.rate),
                fixed_amount=float(config.fixed_amount),
                min_amount=float(config.min_amount) if config.min_amount else None,
                max_amount=float(config.max_amount) if config.max_amount else None,
                tier_brackets=(
                    json.loads(config.tier_brackets) if config.tier_brackets else None
                ),
                billing_day=int(config.billing_day),
                is_active=bool(config.is_active),
                effective_from=config.effective_from,
                effective_until=config.effective_until,
            )
        )

    return result


@router.post(
    "/fees/config",
    response_model=FeeConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee_config(
    config_data: FeeConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new franchise fee configuration"""
    from app.db.multistore_models import FranchiseFeeConfig

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Check if fee type already exists
    existing = (
        db.query(FranchiseFeeConfig)
        .filter(
            FranchiseFeeConfig.tenant_id == tenant.id,
            FranchiseFeeConfig.fee_type == config_data.fee_type,
            FranchiseFeeConfig.is_active == True,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Active fee configuration for '{config_data.fee_type}' already exists",
        )

    config = FranchiseFeeConfig(
        tenant_id=tenant.id,
        fee_type=config_data.fee_type,
        calculation_type=config_data.calculation_type,
        rate=config_data.rate,
        fixed_amount=config_data.fixed_amount,
        min_amount=config_data.min_amount,
        max_amount=config_data.max_amount,
        tier_brackets=(
            json.dumps(config_data.tier_brackets) if config_data.tier_brackets else None
        ),
        billing_day=config_data.billing_day,
        effective_from=config_data.effective_from or datetime.utcnow(),
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(
        f"Franchise fee config created: {config.fee_type} for tenant {tenant.id}"
    )

    return FeeConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        fee_type=config.fee_type,
        calculation_type=config.calculation_type,
        rate=float(config.rate),
        fixed_amount=float(config.fixed_amount),
        min_amount=float(config.min_amount) if config.min_amount else None,
        max_amount=float(config.max_amount) if config.max_amount else None,
        tier_brackets=(
            json.loads(config.tier_brackets) if config.tier_brackets else None
        ),
        billing_day=config.billing_day,
        is_active=config.is_active,
        effective_from=config.effective_from,
        effective_until=config.effective_until,
    )


@router.put("/fees/config/{config_id}", response_model=FeeConfigResponse)
def update_fee_config(
    config_id: int,
    update_data: FeeConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a franchise fee configuration"""
    from app.db.multistore_models import FranchiseFeeConfig

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    config = (
        db.query(FranchiseFeeConfig)
        .filter(
            FranchiseFeeConfig.id == config_id,
            FranchiseFeeConfig.tenant_id == tenant.id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=404, detail="Fee configuration not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    # Handle tier_brackets JSON
    if "tier_brackets" in update_dict:
        update_dict["tier_brackets"] = (
            json.dumps(update_dict["tier_brackets"])
            if update_dict["tier_brackets"]
            else None
        )

    for field, value in update_dict.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return FeeConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        fee_type=config.fee_type,
        calculation_type=config.calculation_type,
        rate=float(config.rate),
        fixed_amount=float(config.fixed_amount),
        min_amount=float(config.min_amount) if config.min_amount else None,
        max_amount=float(config.max_amount) if config.max_amount else None,
        tier_brackets=(
            json.loads(config.tier_brackets) if config.tier_brackets else None
        ),
        billing_day=config.billing_day,
        is_active=config.is_active,
        effective_from=config.effective_from,
        effective_until=config.effective_until,
    )


# ============================================
# Fee Calculation & Records
# ============================================


@router.post("/fees/calculate", response_model=List[FeeCalculationResult])
def calculate_fees(
    request: FeeCalculationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Calculate franchise fees for a period (preview without creating records)"""
    from app.db.multistore_models import FranchiseFeeConfig

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Get fee configs
    configs = (
        db.query(FranchiseFeeConfig)
        .filter(
            FranchiseFeeConfig.tenant_id == tenant.id,
            FranchiseFeeConfig.fee_type.in_(request.fee_types),
            FranchiseFeeConfig.is_active == True,
        )
        .all()
    )

    if not configs:
        raise HTTPException(
            status_code=404, detail="No active fee configurations found"
        )

    # TODO: Get actual sales data from sales table
    # For now, use placeholder data
    gross_sales = 50000.0
    transaction_count = 500

    results = []
    for config in configs:
        calculated, final, min_applied, max_applied = calculate_fee(
            gross_sales=gross_sales,
            transaction_count=transaction_count,
            calculation_type=config.calculation_type,
            rate=float(config.rate),
            fixed_amount=float(config.fixed_amount),
            min_amount=float(config.min_amount) if config.min_amount else None,
            max_amount=float(config.max_amount) if config.max_amount else None,
            tier_brackets=config.tier_brackets,
        )

        results.append(
            FeeCalculationResult(
                fee_type=config.fee_type,
                gross_sales=gross_sales,
                transaction_count=transaction_count,
                rate_applied=float(config.rate),
                calculated_amount=calculated,
                min_applied=min_applied,
                max_applied=max_applied,
                final_amount=final,
            )
        )

    return results


@router.post("/fees/generate", response_model=List[FeeRecordResponse])
def generate_fee_records(
    request: FeeCalculationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate franchise fee records for a period"""
    from app.db.multistore_models import FranchiseFeeConfig, FranchiseFeeRecord

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Get fee configs
    configs = (
        db.query(FranchiseFeeConfig)
        .filter(
            FranchiseFeeConfig.tenant_id == tenant.id,
            FranchiseFeeConfig.fee_type.in_(request.fee_types),
            FranchiseFeeConfig.is_active == True,
        )
        .all()
    )

    if not configs:
        raise HTTPException(
            status_code=404, detail="No active fee configurations found"
        )

    # TODO: Get actual sales data
    gross_sales = 50000.0
    transaction_count = 500

    records = []
    for config in configs:
        # Check if record already exists for this period
        existing = (
            db.query(FranchiseFeeRecord)
            .filter(
                FranchiseFeeRecord.tenant_id == tenant.id,
                FranchiseFeeRecord.config_id == config.id,
                FranchiseFeeRecord.period_start == request.period_start,
                FranchiseFeeRecord.period_end == request.period_end,
            )
            .first()
        )

        if existing:
            records.append(existing)
            continue

        calculated, final, _, _ = calculate_fee(
            gross_sales=gross_sales,
            transaction_count=transaction_count,
            calculation_type=config.calculation_type,
            rate=float(config.rate),
            fixed_amount=float(config.fixed_amount),
            min_amount=float(config.min_amount) if config.min_amount else None,
            max_amount=float(config.max_amount) if config.max_amount else None,
            tier_brackets=config.tier_brackets,
        )

        record = FranchiseFeeRecord(
            tenant_id=tenant.id,
            store_id=request.store_id,
            config_id=config.id,
            period_start=request.period_start,
            period_end=request.period_end,
            gross_sales=gross_sales,
            transaction_count=transaction_count,
            calculated_fee=calculated,
            adjustments=0.0,
            final_fee=final,
            status="pending",
            due_date=request.period_end + timedelta(days=15),
        )
        db.add(record)
        records.append(record)

    db.commit()

    return [FeeRecordResponse.model_validate(r) for r in records]


@router.get("/fees/records", response_model=List[FeeRecordResponse])
def list_fee_records(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List franchise fee records"""
    from app.db.multistore_models import FranchiseFeeRecord

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    query = db.query(FranchiseFeeRecord).filter(
        FranchiseFeeRecord.tenant_id == tenant.id
    )

    if status:
        query = query.filter(FranchiseFeeRecord.status == status)

    if start_date:
        query = query.filter(FranchiseFeeRecord.period_start >= start_date)

    if end_date:
        query = query.filter(FranchiseFeeRecord.period_end <= end_date)

    records = (
        query.order_by(FranchiseFeeRecord.period_start.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [FeeRecordResponse.model_validate(r) for r in records]


@router.post("/fees/records/{record_id}/pay")
def mark_fee_paid(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a fee record as paid"""
    from app.db.multistore_models import FranchiseFeeRecord

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    record = (
        db.query(FranchiseFeeRecord)
        .filter(
            FranchiseFeeRecord.id == record_id,
            FranchiseFeeRecord.tenant_id == tenant.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Fee record not found")

    if record.status == "paid":
        raise HTTPException(status_code=400, detail="Fee already marked as paid")

    record.status = "paid"
    record.paid_at = datetime.utcnow()

    db.commit()

    return {"message": "Fee marked as paid", "record_id": record_id}


# ============================================
# Franchise Summary & Reporting
# ============================================


@router.get("/summary", response_model=FranchiseSummary)
def get_franchise_summary(
    period: str = Query("month", pattern="^(month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get franchise summary with fee breakdown"""
    from app.db.multistore_models import FranchiseFeeRecord

    tenant = get_user_tenant(db, current_user.id)
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for user")

    # Calculate date range
    now = datetime.utcnow()
    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "quarter":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start_date = now.replace(
            month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    else:
        start_date = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

    # Get fee records for period
    records = (
        db.query(FranchiseFeeRecord)
        .filter(
            FranchiseFeeRecord.tenant_id == tenant.id,
            FranchiseFeeRecord.period_start >= start_date,
        )
        .all()
    )

    # Aggregate
    total_gross_sales = sum(float(r.gross_sales) for r in records)
    total_fees_due = sum(float(r.final_fee) for r in records)
    total_fees_paid = sum(float(r.final_fee) for r in records if r.status == "paid")

    # Fee breakdown by type
    fee_breakdown: dict[int, dict[str, Any]] = {}
    for record in records:
        fee_type = int(record.config_id)  # Would need to join to get actual type
        if fee_type not in fee_breakdown:
            fee_breakdown[fee_type] = {"type": f"fee_{fee_type}", "amount": 0.0}
        fee_breakdown[fee_type]["amount"] += float(record.final_fee)

    # Store count
    store_count = (
        db.query(func.count(Store.id))
        .filter(Store.tenant_id == tenant.id, Store.is_active == True)
        .scalar()
        or 0
    )

    return FranchiseSummary(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        period=period,
        total_gross_sales=total_gross_sales,
        total_fees_due=total_fees_due,
        total_fees_paid=total_fees_paid,
        outstanding_balance=total_fees_due - total_fees_paid,
        stores_count=store_count,
        fee_breakdown=list(fee_breakdown.values()),
    )
