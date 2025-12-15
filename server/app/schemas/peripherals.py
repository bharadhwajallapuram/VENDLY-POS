"""
Vendly POS - Printer & Barcode Schemas
Pydantic models for printer/peripheral API requests and responses
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PrinterType(str, Enum):
    """Printer type"""

    USB = "usb"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"


class PrinterStatus(str, Enum):
    """Printer status"""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    OUT_OF_PAPER = "out_of_paper"
    UNKNOWN = "unknown"


class PrinterConfigIn(BaseModel):
    """Printer configuration input"""

    name: str = Field(..., description="Printer name")
    type: PrinterType = Field(..., description="Printer type (usb, network, bluetooth)")
    ip_address: Optional[str] = Field(
        None, description="IP address for network printers"
    )
    port: int = Field(default=9100, description="Port for network printers")
    usb_vendor_id: Optional[str] = Field(None, description="USB vendor ID (hex)")
    usb_product_id: Optional[str] = Field(None, description="USB product ID (hex)")
    baudrate: int = Field(default=115200, description="Serial baudrate")
    timeout: int = Field(default=5, description="Connection timeout in seconds")
    paper_width: int = Field(default=80, description="Paper width in mm (58 or 80)")
    is_default: bool = Field(default=False, description="Set as default printer")
    is_active: bool = Field(default=True, description="Printer is active")


class PrinterConfigOut(PrinterConfigIn):
    """Printer configuration output"""

    id: str = Field(..., description="Printer ID")
    status: PrinterStatus = Field(..., description="Current printer status")


class PrinterListResponse(BaseModel):
    """Printer list response"""

    printers: List[PrinterConfigOut]
    total: int = Field(..., description="Total printers")


class PrintReceiptRequest(BaseModel):
    """Print receipt request"""

    receipt_id: Optional[int] = Field(
        None, description="Sale receipt ID (alternative to receipt_data)"
    )
    printer_id: Optional[str] = Field(
        None, description="Printer ID (uses default if not specified)"
    )
    copies: int = Field(default=1, ge=1, le=10, description="Number of copies")
    paper_width: int = Field(default=80, description="Paper width in mm")


class PrintReceiptResponse(BaseModel):
    """Print receipt response"""

    success: bool = Field(...)
    message: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
    printer_id: Optional[str] = Field(None)
    copies: Optional[int] = Field(None)


class CashDrawerRequest(BaseModel):
    """Cash drawer request"""

    printer_id: Optional[str] = Field(
        None, description="Printer ID (uses default if not specified)"
    )


class CashDrawerResponse(BaseModel):
    """Cash drawer response"""

    success: bool = Field(...)
    message: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
    printer_id: Optional[str] = Field(None)


class PaperCutRequest(BaseModel):
    """Paper cut request"""

    printer_id: Optional[str] = Field(None, description="Printer ID")
    partial: bool = Field(default=False, description="Partial cut (default: full cut)")


class PaperCutResponse(BaseModel):
    """Paper cut response"""

    success: bool = Field(...)
    message: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
    printer_id: Optional[str] = Field(None)
    partial: Optional[bool] = Field(None, description="Partial cut flag")


class PrinterTestResponse(BaseModel):
    """Printer test response"""

    success: bool = Field(...)
    message: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
    printer_id: Optional[str] = Field(None)


class PrinterStatusResponse(BaseModel):
    """Printer status response"""

    id: str = Field(...)
    name: str = Field(...)
    type: PrinterType = Field(...)
    status: PrinterStatus = Field(...)
    ip_address: Optional[str] = Field(None)
    port: Optional[int] = Field(None)
    is_active: bool = Field(...)
    is_default: bool = Field(...)


class BarcodeFormat(str, Enum):
    """Barcode format"""

    CODE128 = "code128"
    CODE39 = "code39"
    EAN13 = "ean13"
    EAN8 = "ean8"
    UPC_A = "upca"
    UPC_E = "upce"
    QR_CODE = "qr"
    DATA_MATRIX = "datamatrix"


class GenerateBarcodeRequest(BaseModel):
    """Generate barcode request"""

    data: str = Field(..., description="Data to encode", min_length=1, max_length=255)
    format: BarcodeFormat = Field(
        default=BarcodeFormat.CODE128, description="Barcode format"
    )
    width: int = Field(
        default=200, ge=100, le=1000, description="Image width in pixels"
    )
    height: int = Field(
        default=100, ge=50, le=1000, description="Image height in pixels"
    )
    include_text: bool = Field(default=True, description="Include barcode text")


class GenerateBarcodeResponse(BaseModel):
    """Generate barcode response"""

    success: bool = Field(...)
    format: Optional[str] = Field(None)
    data: Optional[str] = Field(None)
    image_base64: Optional[str] = Field(None, description="Base64 encoded PNG image")
    svg: Optional[str] = Field(None, description="SVG version of barcode")
    width: Optional[int] = Field(None)
    height: Optional[int] = Field(None)
    error: Optional[str] = Field(None)


class ValidateBarcodeRequest(BaseModel):
    """Validate barcode request"""

    data: str = Field(..., description="Data to validate")
    format: BarcodeFormat = Field(
        default=BarcodeFormat.CODE128, description="Barcode format"
    )


class ValidateBarcodeResponse(BaseModel):
    """Validate barcode response"""

    valid: bool = Field(...)
    message: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
