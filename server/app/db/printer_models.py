"""
Vendly POS - Printer Models
Database models for printer configuration and status tracking
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.models import Base


class PrinterTypeEnum(str, Enum):
    """Printer type"""

    USB = "usb"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"


class PrinterStatusEnum(str, Enum):
    """Printer status"""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    OUT_OF_PAPER = "out_of_paper"
    UNKNOWN = "unknown"


class Printer(Base):
    """Printer configuration"""

    __tablename__ = "printers"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Printer type and connection
    printer_type = Column(String(50), nullable=False)  # usb, network, bluetooth
    ip_address = Column(String(255), nullable=True)  # For network printers
    port = Column(Integer, default=9100, nullable=True)  # For network printers

    # USB configuration
    usb_vendor_id = Column(String(10), nullable=True)  # Hex vendor ID
    usb_product_id = Column(String(10), nullable=True)  # Hex product ID

    # Serial/Bluetooth configuration
    baudrate = Column(Integer, default=115200)
    timeout = Column(Integer, default=5)  # seconds

    # Paper width in mm (58 or 80)
    paper_width = Column(Integer, default=80)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False, index=True)
    last_status = Column(String(50), nullable=True)
    last_tested_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Printer(id={self.id}, name={self.name}, type={self.printer_type})>"


class PrinterUsageLog(Base):
    """Log of printer usage (receipts printed, test prints, etc.)"""

    __tablename__ = "printer_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(String(100), nullable=False, index=True)

    # What was printed
    operation_type = Column(
        String(50), nullable=False
    )  # receipt, test_print, cash_drawer, cut_paper
    sale_id = Column(Integer, nullable=True, index=True)  # If printing receipt

    # Status
    success = Column(Boolean, nullable=False)
    status_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Details
    copies_printed = Column(Integer, default=1)
    paper_width = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<PrinterUsageLog(id={self.id}, printer_id={self.printer_id}, operation={self.operation_type})>"
