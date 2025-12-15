# ===========================================
# Tax Service - GST/VAT Calculation & Management
# ===========================================

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db import models as m


class TaxService:
    """
    Service for managing tax rates, configurations, and calculations
    Supports GST (India, Australia), VAT (UK, EU), and Sales Tax (US, Canada)
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Tax Rate Management ====================

    def create_tax_rate(
        self,
        region: str,
        tax_type: str,
        name: str,
        rate: float,
        state_code: Optional[str] = None,
        description: Optional[str] = None,
        effective_from: Optional[datetime] = None,
        effective_to: Optional[datetime] = None,
    ) -> m.TaxRate:
        """Create a new tax rate"""
        tax_rate = m.TaxRate(
            region=region,
            tax_type=tax_type,
            name=name,
            rate=rate,
            state_code=state_code,
            description=description,
            effective_from=effective_from or datetime.now(),
            effective_to=effective_to,
            is_active=True,
        )
        self.db.add(tax_rate)
        self.db.commit()
        self.db.refresh(tax_rate)
        return tax_rate

    def get_tax_rates(
        self,
        region: Optional[str] = None,
        tax_type: Optional[str] = None,
        is_active: bool = True,
    ) -> List[m.TaxRate]:
        """Get tax rates with optional filtering"""
        query = self.db.query(m.TaxRate)

        if is_active:
            query = query.filter(m.TaxRate.is_active == True)
            # Check effective dates
            now = datetime.now()
            query = query.filter(m.TaxRate.effective_from <= now)
            query = query.filter(
                (m.TaxRate.effective_to.is_(None)) | (m.TaxRate.effective_to >= now)
            )

        if region:
            query = query.filter(m.TaxRate.region == region)

        if tax_type:
            query = query.filter(m.TaxRate.tax_type == tax_type)

        return query.all()

    def get_tax_rate(self, tax_rate_id: int) -> Optional[m.TaxRate]:
        """Get a specific tax rate"""
        return self.db.query(m.TaxRate).filter(m.TaxRate.id == tax_rate_id).first()

    def update_tax_rate(
        self,
        tax_rate_id: int,
        rate: Optional[float] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> Optional[m.TaxRate]:
        """Update a tax rate"""
        tax_rate = self.get_tax_rate(tax_rate_id)
        if not tax_rate:
            return None

        if rate is not None:
            tax_rate.rate = rate
        if is_active is not None:
            tax_rate.is_active = is_active
        if description is not None:
            tax_rate.description = description
        tax_rate.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(tax_rate)
        return tax_rate

    # ==================== Tax Configuration ====================

    def get_or_create_config(
        self,
        user_id: int,
        region: str,
    ) -> m.TaxConfiguration:
        """Get or create tax configuration for a user"""
        config = (
            self.db.query(m.TaxConfiguration)
            .filter(
                m.TaxConfiguration.user_id == user_id,
                m.TaxConfiguration.region == region,
            )
            .first()
        )

        if not config:
            # Get default tax rate for region
            default_rate = (
                self.db.query(m.TaxRate)
                .filter(m.TaxRate.region == region, m.TaxRate.is_active == True)
                .first()
            )

            config = m.TaxConfiguration(
                user_id=user_id,
                region=region,
                default_tax_rate_id=default_rate.id if default_rate else None,
                rounding_method="round",
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

        return config

    def update_config(
        self,
        config_id: int,
        tax_id: Optional[str] = None,
        is_tax_exempt: Optional[bool] = None,
        enable_compound_tax: Optional[bool] = None,
        enable_reverse_charge: Optional[bool] = None,
        enable_tax_invoice: Optional[bool] = None,
        rounding_method: Optional[str] = None,
    ) -> Optional[m.TaxConfiguration]:
        """Update tax configuration"""
        config = (
            self.db.query(m.TaxConfiguration)
            .filter(m.TaxConfiguration.id == config_id)
            .first()
        )
        if not config:
            return None

        if tax_id is not None:
            config.tax_id = tax_id
        if is_tax_exempt is not None:
            config.is_tax_exempt = is_tax_exempt
        if enable_compound_tax is not None:
            config.enable_compound_tax = enable_compound_tax
        if enable_reverse_charge is not None:
            config.enable_reverse_charge = enable_reverse_charge
        if enable_tax_invoice is not None:
            config.enable_tax_invoice = enable_tax_invoice
        if rounding_method is not None:
            config.rounding_method = rounding_method

        config.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(config)
        return config

    # ==================== Tax Calculation ====================

    def calculate_tax(
        self,
        subtotal: float,
        tax_rate_id: int,
        is_compound: bool = False,
        base_tax_amount: Optional[float] = None,
    ) -> dict:
        """
        Calculate tax for a given subtotal

        Args:
            subtotal: Base amount to tax
            tax_rate_id: ID of tax rate to apply
            is_compound: Whether this is a compound tax (applies on subtotal + previous tax)
            base_tax_amount: For compound tax, the previous tax amount

        Returns:
            Dictionary with tax_amount, tax_rate, tax_type, and taxable_base
        """
        tax_rate = self.get_tax_rate(tax_rate_id)
        if not tax_rate:
            return {
                "tax_amount": 0.0,
                "tax_rate": 0.0,
                "tax_type": "none",
                "taxable_base": subtotal,
            }

        # Determine taxable base
        if is_compound and base_tax_amount:
            taxable_base = subtotal + base_tax_amount
        else:
            taxable_base = subtotal

        # Calculate tax
        tax_decimal = Decimal(str(taxable_base)) * (
            Decimal(str(tax_rate.rate)) / Decimal("100")
        )

        # Apply rounding based on configuration
        tax_amount = float(
            tax_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        return {
            "tax_amount": tax_amount,
            "tax_rate": tax_rate.rate,
            "tax_type": tax_rate.tax_type,
            "taxable_base": taxable_base,
            "tax_rate_id": tax_rate_id,
        }

    def calculate_compound_tax(
        self,
        subtotal: float,
        tax_rate_ids: List[int],
    ) -> dict:
        """
        Calculate compound tax (e.g., CGST + SGST in India GST)

        Args:
            subtotal: Base amount
            tax_rate_ids: List of tax rate IDs to apply in order

        Returns:
            Dictionary with total tax, breakdown, and calculations
        """
        total_tax = 0.0
        calculations: List[dict] = []
        taxable_base = subtotal

        for i, tax_rate_id in enumerate(tax_rate_ids):
            is_compound = i > 0  # Second and subsequent taxes are compound
            base_tax = calculations[i - 1]["tax_amount"] if i > 0 else None

            calc = self.calculate_tax(
                subtotal=subtotal,
                tax_rate_id=tax_rate_id,
                is_compound=is_compound,
                base_tax_amount=base_tax,
            )
            calculations.append(calc)
            total_tax += calc["tax_amount"]

        return {
            "total_tax": total_tax,
            "subtotal": subtotal,
            "total_with_tax": subtotal + total_tax,
            "calculations": calculations,
        }

    def record_calculation(
        self,
        sale_id: int,
        tax_rate_id: int,
        subtotal: float,
        tax_amount: float,
        tax_rate: float,
        tax_type: str,
        is_compound: bool = False,
        base_calculation_id: Optional[int] = None,
    ) -> m.TaxCalculation:
        """Record a tax calculation for audit trail"""
        calc = m.TaxCalculation(
            sale_id=sale_id,
            tax_rate_id=tax_rate_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            tax_type=tax_type,
            is_compound=is_compound,
            base_calculation_id=base_calculation_id,
        )
        self.db.add(calc)
        self.db.commit()
        self.db.refresh(calc)
        return calc

    def get_tax_calculations(self, sale_id: int) -> List[m.TaxCalculation]:
        """Get all tax calculations for a sale"""
        return (
            self.db.query(m.TaxCalculation)
            .filter(m.TaxCalculation.sale_id == sale_id)
            .order_by(m.TaxCalculation.id)
            .all()
        )

    # ==================== Tax Reporting ====================

    def get_tax_report(
        self,
        region: str,
        tax_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get tax summary report for a region"""
        query = (
            self.db.query(
                m.TaxCalculation.tax_type,
                m.TaxCalculation.tax_rate,
                m.TaxRate.name,
            )
            .join(m.TaxRate, m.TaxCalculation.tax_rate_id == m.TaxRate.id)
            .filter(m.TaxRate.region == region)
        )

        if tax_type:
            query = query.filter(m.TaxCalculation.tax_type == tax_type)

        if start_date:
            query = query.filter(m.TaxCalculation.created_at >= start_date)

        if end_date:
            query = query.filter(m.TaxCalculation.created_at <= end_date)

        calcs = query.all()

        # Group by tax type
        by_type = {}
        total_tax = 0.0
        total_subtotal = 0.0

        for calc in calcs:
            tax_type_name = calc.tax_type
            if tax_type_name not in by_type:
                by_type[tax_type_name] = {
                    "name": calc.name,
                    "rate": calc.tax_rate,
                    "total_tax": 0.0,
                    "total_subtotal": 0.0,
                    "count": 0,
                }
            by_type[tax_type_name]["total_tax"] += calc.tax_amount
            by_type[tax_type_name]["total_subtotal"] += calc.subtotal
            by_type[tax_type_name]["count"] += 1
            total_tax += calc.tax_amount
            total_subtotal += calc.subtotal

        return {
            "region": region,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "total_subtotal": total_subtotal,
            "total_tax": total_tax,
            "total_with_tax": total_subtotal + total_tax,
            "by_type": by_type,
        }

    def get_tax_by_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get tax summary by tax rate"""
        query = self.db.query(m.TaxCalculation)

        if start_date:
            query = query.filter(m.TaxCalculation.created_at >= start_date)

        if end_date:
            query = query.filter(m.TaxCalculation.created_at <= end_date)

        calcs = query.all()

        by_rate: dict = {}
        for calc in calcs:
            rate_key = f"{float(Decimal(str(calc.tax_rate)))}%"
            if rate_key not in by_rate:
                by_rate[rate_key] = {
                    "rate": float(Decimal(str(calc.tax_rate))),
                    "type": calc.tax_type,
                    "total_tax": 0.0,
                    "total_subtotal": 0.0,
                    "count": 0,
                }
            by_rate[rate_key]["total_tax"] += float(Decimal(str(calc.tax_amount)))
            by_rate[rate_key]["total_subtotal"] += float(Decimal(str(calc.subtotal)))
            by_rate[rate_key]["count"] += 1

        return by_rate


# ==================== Default Tax Rates Setup ====================


def setup_default_tax_rates(db: Session):
    """Initialize default tax rates for common regions"""
    defaults = [
        # India GST
        {"region": "in", "tax_type": "gst", "name": "CGST", "rate": 9.0},
        {"region": "in", "tax_type": "gst", "name": "SGST", "rate": 9.0},
        {"region": "in", "tax_type": "gst", "name": "IGST", "rate": 18.0},
        # Australia GST
        {"region": "au", "tax_type": "gst", "name": "GST", "rate": 10.0},
        # New Zealand GST
        {"region": "nz", "tax_type": "gst", "name": "GST", "rate": 15.0},
        # Singapore GST
        {"region": "sg", "tax_type": "gst", "name": "GST", "rate": 8.0},
        # UK VAT
        {"region": "uk", "tax_type": "vat", "name": "Standard VAT", "rate": 20.0},
        {"region": "uk", "tax_type": "vat", "name": "Reduced VAT", "rate": 5.0},
        # Canada GST/HST
        {"region": "ca", "tax_type": "gst", "name": "GST", "rate": 5.0},
        {"region": "ca", "tax_type": "gst", "name": "HST", "rate": 13.0},
        # US Sales Tax (varies by state, example for California)
        {
            "region": "us",
            "tax_type": "sales_tax",
            "name": "CA Sales Tax",
            "rate": 7.25,
            "state_code": "CA",
        },
    ]

    for default in defaults:
        existing = (
            db.query(m.TaxRate)
            .filter(
                m.TaxRate.region == default["region"],
                m.TaxRate.name == default["name"],
            )
            .first()
        )
        if not existing:
            tax_rate = m.TaxRate(
                region=default["region"],
                tax_type=default["tax_type"],
                name=default["name"],
                rate=default["rate"],
                state_code=default.get("state_code"),
                is_active=True,
            )
            db.add(tax_rate)

    db.commit()
