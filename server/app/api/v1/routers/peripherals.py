"""
Vendly POS - Peripherals Router
REST API endpoints for thermal printers, cash drawers, barcode generation, etc.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permission
from app.schemas.peripherals import (
    CashDrawerRequest,
    CashDrawerResponse,
    GenerateBarcodeRequest,
    GenerateBarcodeResponse,
    PaperCutRequest,
    PaperCutResponse,
    PrinterConfigIn,
    PrinterConfigOut,
    PrinterListResponse,
    PrinterStatusResponse,
    PrinterTestResponse,
    PrintReceiptRequest,
    PrintReceiptResponse,
    ValidateBarcodeRequest,
    ValidateBarcodeResponse,
)
from app.services.barcode_service import barcode_service
from app.services.printer_service import PrinterConfig, PrinterType, printer_service
from app.services.receipt import Receipt, ReceiptItem

router = APIRouter(prefix="/peripherals", tags=["peripherals"])


# ====================
# Printer Management
# ====================


@router.post(
    "/printers/register",
    response_model=PrinterConfigOut,
    status_code=status.HTTP_201_CREATED,
)
def register_printer(
    config: PrinterConfigIn,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """
    Register a new printer

    Supports:
    - USB thermal printers
    - Network thermal printers (IP + port)
    - Bluetooth printers
    """
    try:
        # Generate printer ID
        printer_id = f"printer_{len(printer_service.printers) + 1}"

        # Create printer config
        printer_config = PrinterConfig(
            id=printer_id,
            name=config.name,
            type=config.type,
            ip_address=config.ip_address,
            port=config.port,
            usb_vendor_id=config.usb_vendor_id,
            usb_product_id=config.usb_product_id,
            baudrate=config.baudrate,
            timeout=config.timeout,
            paper_width=config.paper_width,
            is_default=config.is_default,
            is_active=config.is_active,
        )

        # Register printer
        if not printer_service.register_printer(printer_config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register printer",
            )

        # Get status
        status_val = printer_service.check_printer_status(printer_id)

        return PrinterConfigOut(
            id=printer_id,
            name=config.name,
            type=config.type,
            ip_address=config.ip_address,
            port=config.port,
            usb_vendor_id=config.usb_vendor_id,
            usb_product_id=config.usb_product_id,
            baudrate=config.baudrate,
            timeout=config.timeout,
            paper_width=config.paper_width,
            is_default=config.is_default,
            is_active=config.is_active,
            status=status_val,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/printers", response_model=PrinterListResponse)
def list_printers(
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """List all registered printers"""
    printers_list = printer_service.list_printers()
    return PrinterListResponse(printers=printers_list, total=len(printers_list))


@router.get("/printers/{printer_id}/status", response_model=PrinterStatusResponse)
def get_printer_status(
    printer_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get printer status"""
    printer = printer_service.get_printer(printer_id)
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found"
        )

    status_val = printer_service.check_printer_status(printer_id)

    return PrinterStatusResponse(
        id=printer.id,
        name=printer.name,
        type=printer.type,
        status=status_val,
        ip_address=printer.ip_address,
        port=printer.port,
        is_active=printer.is_active,
        is_default=printer.is_default,
    )


@router.post("/printers/{printer_id}/test", response_model=PrinterTestResponse)
def test_printer(
    printer_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """Test printer connection by printing a test page"""
    try:
        result = printer_service.test_print(printer_id)
        return PrinterTestResponse(
            success=result.get("success", False),
            message=result.get("message"),
            error=result.get("error"),
            printer_id=result.get("printer_id"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ====================
# Receipt Printing
# ====================


@router.post("/printers/print-receipt", response_model=PrintReceiptResponse)
def print_receipt(
    request: PrintReceiptRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Print receipt to thermal printer

    Supports:
    - USB thermal printers
    - Network thermal printers
    - Multiple copies
    - Different paper widths (58mm, 80mm)
    """
    from app.db import models as m

    try:
        # Get sale
        if not request.receipt_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="receipt_id is required"
            )

        sale = db.get(m.Sale, request.receipt_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found"
            )

        # Build receipt object
        receipt_items = []
        for item in sale.items:
            product = db.get(m.Product, item.product_id)
            receipt_items.append(
                ReceiptItem(
                    name=product.name if product else f"Product #{item.product_id}",
                    quantity=item.quantity,
                    unit_price=float(item.unit_price),
                    total=float(item.subtotal),
                )
            )

        # Get cashier name
        cashier = db.get(m.User, sale.user_id)
        cashier_name = cashier.full_name or cashier.email if cashier else "Unknown"

        # Get customer if any
        customer_name = None
        if sale.customer_id:
            customer = db.get(m.Customer, sale.customer_id)
            customer_name = customer.name if customer else None

        # Calculate tax rate
        tax_rate = 8.0
        if sale.subtotal > 0:
            tax_rate = round((float(sale.tax) / float(sale.subtotal)) * 100, 2)

        # Build receipt
        receipt = Receipt(
            receipt_number=f"R-{sale.id:06d}",
            date=sale.created_at,
            items=receipt_items,
            subtotal=float(sale.subtotal),
            tax_amount=float(sale.tax),
            tax_rate=tax_rate,
            total=float(sale.total),
            payment_method=sale.payment_method or "cash",
            amount_paid=float(sale.total),
            change=0.0,
            cashier_name=cashier_name,
            customer_name=customer_name,
        )

        # Print
        result = printer_service.print_receipt(
            receipt,
            printer_id=request.printer_id,
            copies=request.copies,
            paper_width=request.paper_width,
        )

        return PrintReceiptResponse(
            success=result.get("success", False),
            message=result.get("message"),
            error=result.get("error"),
            printer_id=result.get("printer_id"),
            copies=result.get("copies"),
        )
    except HTTPException:
        raise
    except Exception as e:
        return PrintReceiptResponse(
            success=False,
            error=str(e),
        )


# ====================
# Cash Drawer
# ====================


@router.post("/cash-drawer/open", response_model=CashDrawerResponse)
def open_cash_drawer(
    request: CashDrawerRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """
    Open cash drawer

    Sends ESC/POS cash drawer open command to printer.
    Requires printer connected to cash drawer.
    """
    result = printer_service.open_cash_drawer(printer_id=request.printer_id)
    return CashDrawerResponse(
        success=result.get("success", False),
        message=result.get("message"),
        error=result.get("error"),
        printer_id=result.get("printer_id"),
    )


# ====================
# Paper Cutting
# ====================


@router.post("/printers/{printer_id}/cut-paper", response_model=PaperCutResponse)
def cut_paper(
    printer_id: str,
    request: PaperCutRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    """
    Cut paper on thermal printer

    Supports:
    - Full cut (default)
    - Partial cut
    """
    result = printer_service.cut_paper(
        printer_id=printer_id,
        partial=request.partial,
    )
    return PaperCutResponse(
        success=result.get("success", False),
        message=result.get("message"),
        error=result.get("error"),
        printer_id=result.get("printer_id"),
        partial=result.get("partial"),
    )


# ====================
# Barcode Generation & Validation
# ====================


@router.post("/barcodes/generate", response_model=GenerateBarcodeResponse)
def generate_barcode(
    request: GenerateBarcodeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Generate barcode image

    Supports:
    - Code128, Code39 (linear barcodes)
    - EAN-13, EAN-8, UPC-A, UPC-E (product codes)
    - QR Code (2D barcode)

    Returns:
    - Base64 encoded PNG image
    - SVG version for web display
    """
    try:
        result = barcode_service.generate_barcode(
            data=request.data,
            format=request.format,
            width=request.width,
            height=request.height,
            include_text=request.include_text,
        )

        return GenerateBarcodeResponse(
            success=result.get("success", False),
            format=result.get("format"),
            data=result.get("data"),
            image_base64=result.get("image_base64"),
            svg=result.get("svg"),
            width=result.get("width"),
            height=result.get("height"),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/barcodes/validate", response_model=ValidateBarcodeResponse)
def validate_barcode(
    request: ValidateBarcodeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Validate barcode data for specific format

    Validates:
    - Format compatibility
    - Length requirements
    - Character set
    - Checksum (if applicable)
    """
    try:
        result = barcode_service.validate_barcode(
            data=request.data,
            format=request.format,
        )

        return ValidateBarcodeResponse(
            valid=result.get("valid", False),
            message=result.get("message"),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/barcodes/formats")
def list_barcode_formats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List supported barcode formats"""
    from app.schemas.peripherals import BarcodeFormat

    return {
        "formats": [
            {
                "code": fmt.value,
                "name": fmt.name.replace("_", " "),
                "type": "linear" if fmt != BarcodeFormat.QR_CODE else "2d",
                "description": {
                    "code128": "Alphanumeric barcode, most flexible",
                    "code39": "Alphanumeric barcode, older standard",
                    "ean13": "13-digit product code (standard)",
                    "ean8": "8-digit product code (compact)",
                    "upca": "12-digit product code (North America)",
                    "upce": "6-digit product code (compressed UPC)",
                    "qr": "2D QR code (high capacity, scannable by phones)",
                    "datamatrix": "2D Data Matrix code",
                }.get(fmt.value, ""),
            }
            for fmt in BarcodeFormat
        ]
    }
