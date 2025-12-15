"""
Vendly POS - Printer Service
Handles thermal printer control, ESC/POS commands, cash drawer, receipt cutter, etc.
"""

import logging
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config_loader import get_receipt_settings, get_store_info
from app.services.receipt import (
    Receipt,
    ReceiptItem,
    generate_receipt_html,
    generate_receipt_text,
)

logger = logging.getLogger(__name__)


class PrinterType(str, Enum):
    """Supported printer types"""

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


@dataclass
class PrinterConfig:
    """Printer configuration"""

    id: str
    name: str
    type: PrinterType
    ip_address: Optional[str] = None
    port: int = 9100
    usb_vendor_id: Optional[str] = None
    usb_product_id: Optional[str] = None
    baudrate: int = 115200
    timeout: int = 5
    paper_width: int = 80  # 58mm or 80mm
    is_default: bool = False
    is_active: bool = True


class ESCPOSCommands:
    """ESC/POS Command Constants"""

    # Initialize printer
    RESET = b"\x1b\x40"
    INIT = b"\x1b\x40"

    # Text formatting
    BOLD_ON = b"\x1b\x45\x01"
    BOLD_OFF = b"\x1b\x45\x00"
    UNDERLINE_ON = b"\x1b\x2d\x01"
    UNDERLINE_OFF = b"\x1b\x2d\x00"

    # Font sizes
    FONT_SIZE_NORMAL = b"\x1b\x21\x00"
    FONT_SIZE_DOUBLE_HEIGHT = b"\x1b\x21\x10"
    FONT_SIZE_DOUBLE_WIDTH = b"\x1b\x21\x20"
    FONT_SIZE_DOUBLE = b"\x1b\x21\x30"

    # Text alignment
    ALIGN_LEFT = b"\x1b\x61\x00"
    ALIGN_CENTER = b"\x1b\x61\x01"
    ALIGN_RIGHT = b"\x1b\x61\x02"

    # Line spacing
    LINE_SPACING_DEFAULT = b"\x1b\x32"
    LINE_SPACING_CUSTOM = b"\x1b\x33"

    # Paper cutting
    PAPER_CUT_FULL = b"\x1d\x56\x00"
    PAPER_CUT_PARTIAL = b"\x1d\x56\x01"

    # Cash drawer
    CASH_DRAWER_OPEN = b"\x1b\x70\x00\x19\x19"

    # Line feed
    LF = b"\n"
    CR = b"\r"

    # Beep
    BEEP = b"\x1b\x42\x09\x09"

    # Status check
    GET_STATUS = b"\x1d\x72\x01"


class PrinterService:
    """Service for controlling thermal printers and peripherals"""

    def __init__(self):
        self.printers: Dict[str, PrinterConfig] = {}
        self.active_connections: Dict[str, socket.socket] = {}

    def register_printer(self, config: PrinterConfig) -> bool:
        """Register a new printer"""
        try:
            self.printers[config.id] = config
            logger.info(f"Registered printer: {config.name} ({config.id})")
            return True
        except Exception as e:
            logger.error(f"Error registering printer: {e}")
            return False

    def get_printer(self, printer_id: str) -> Optional[PrinterConfig]:
        """Get printer config by ID"""
        return self.printers.get(printer_id)

    def list_printers(self) -> List[Dict[str, Any]]:
        """List all registered printers"""
        printers_list = []
        for printer_id, config in self.printers.items():
            status = self.check_printer_status(printer_id)
            printers_list.append(
                {
                    "id": printer_id,
                    "name": config.name,
                    "type": config.type.value,
                    "ip_address": config.ip_address,
                    "port": config.port,
                    "status": status.value,
                    "is_default": config.is_default,
                    "is_active": config.is_active,
                }
            )
        return printers_list

    def check_printer_status(self, printer_id: str) -> PrinterStatus:
        """Check printer status"""
        try:
            printer = self.get_printer(printer_id)
            if not printer or not printer.is_active:
                return PrinterStatus.OFFLINE

            if printer.type == PrinterType.NETWORK:
                return self._check_network_printer_status(printer)
            elif printer.type == PrinterType.USB:
                return self._check_usb_printer_status(printer)
            else:
                return PrinterStatus.UNKNOWN
        except Exception as e:
            logger.error(f"Error checking printer status: {e}")
            return PrinterStatus.ERROR

    def _check_network_printer_status(self, printer: PrinterConfig) -> PrinterStatus:
        """Check network printer status via socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(printer.timeout)
            result = sock.connect_ex((printer.ip_address, printer.port))
            sock.close()

            if result == 0:
                return PrinterStatus.ONLINE
            else:
                return PrinterStatus.OFFLINE
        except Exception:
            return PrinterStatus.OFFLINE

    def _check_usb_printer_status(self, printer: PrinterConfig) -> PrinterStatus:
        """Check USB printer status"""
        try:
            # Try to import pyusb for USB device detection
            try:
                import usb.core

                devices = usb.core.find(find_all=True)
                vendor_id = (
                    int(printer.usb_vendor_id, 16) if printer.usb_vendor_id else None
                )
                product_id = (
                    int(printer.usb_product_id, 16) if printer.usb_product_id else None
                )

                if vendor_id and product_id:
                    device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
                    return PrinterStatus.ONLINE if device else PrinterStatus.OFFLINE
                return PrinterStatus.UNKNOWN
            except ImportError:
                # pyusb not installed, assume online
                return PrinterStatus.ONLINE
        except Exception:
            return PrinterStatus.ERROR

    def print_receipt(
        self,
        receipt: Receipt,
        printer_id: Optional[str] = None,
        copies: int = 1,
        paper_width: int = 80,
    ) -> Dict[str, Any]:
        """
        Print receipt to thermal printer

        Args:
            receipt: Receipt object to print
            printer_id: ID of printer to use (default printer if None)
            copies: Number of copies to print
            paper_width: Paper width in mm (58 or 80)
        """
        try:
            if not printer_id:
                # Find default printer
                default_printer = next(
                    (p for p in self.printers.values() if p.is_default), None
                )
                if not default_printer:
                    return {
                        "success": False,
                        "error": "No printer configured. Set a default printer first.",
                    }
                printer_id = default_printer.id

            printer = self.get_printer(printer_id)
            if not printer:
                return {"success": False, "error": f"Printer {printer_id} not found"}

            if not printer.is_active:
                return {"success": False, "error": f"Printer {printer_id} is inactive"}

            # Generate receipt text with proper width
            receipt_text = generate_receipt_text(
                receipt, width=paper_width // 3
            )  # ~40 chars for 80mm

            # Build ESC/POS output
            output = ESCPOSCommands.INIT
            output += ESCPOSCommands.FONT_SIZE_NORMAL

            for _ in range(copies):
                # Print receipt text
                output += receipt_text.encode("utf-8")
                output += ESCPOSCommands.LF

                # Paper cut
                output += ESCPOSCommands.PAPER_CUT_FULL
                output += ESCPOSCommands.LF

            # Send to printer
            if printer.type == PrinterType.NETWORK:
                success = self._send_to_network_printer(printer, output)
            elif printer.type == PrinterType.USB:
                success = self._send_to_usb_printer(printer, output)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported printer type: {printer.type}",
                }

            if success:
                logger.info(f"Receipt printed successfully on {printer.name}")
                return {
                    "success": True,
                    "message": f"Printed {copies} copy(ies) on {printer.name}",
                    "printer_id": printer_id,
                    "copies": copies,
                }
            else:
                return {"success": False, "error": f"Failed to print on {printer.name}"}
        except Exception as e:
            logger.error(f"Error printing receipt: {e}")
            return {"success": False, "error": str(e)}

    def _send_to_network_printer(self, printer: PrinterConfig, data: bytes) -> bool:
        """Send data to network printer"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(printer.timeout)
            sock.connect((printer.ip_address, printer.port))
            sock.sendall(data)
            sock.close()
            return True
        except Exception as e:
            logger.error(f"Error sending to network printer: {e}")
            return False

    def _send_to_usb_printer(self, printer: PrinterConfig, data: bytes) -> bool:
        """Send data to USB printer"""
        try:
            try:
                import usb.core
                import usb.util

                vendor_id = (
                    int(printer.usb_vendor_id, 16) if printer.usb_vendor_id else None
                )
                product_id = (
                    int(printer.usb_product_id, 16) if printer.usb_product_id else None
                )

                if not (vendor_id and product_id):
                    return False

                device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
                if not device:
                    return False

                # Find endpoint
                cfg = device.get_active_configuration()
                intf = cfg[(0, 0)]
                ep = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(
                        e.bEndpointAddress
                    )
                    == usb.util.ENDPOINT_OUT,
                )

                if ep:
                    ep.write(data)
                    return True
                return False
            except ImportError:
                logger.warning("pyusb not installed. USB printer support disabled.")
                return False
        except Exception as e:
            logger.error(f"Error sending to USB printer: {e}")
            return False

    def open_cash_drawer(self, printer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Open cash drawer via printer

        Args:
            printer_id: ID of printer connected to cash drawer
        """
        try:
            if not printer_id:
                # Find default printer
                default_printer = next(
                    (p for p in self.printers.values() if p.is_default), None
                )
                if not default_printer:
                    return {"success": False, "error": "No printer configured"}
                printer_id = default_printer.id

            printer = self.get_printer(printer_id)
            if not printer:
                return {"success": False, "error": f"Printer {printer_id} not found"}

            # Send cash drawer open command
            output = ESCPOSCommands.CASH_DRAWER_OPEN
            output += ESCPOSCommands.BEEP

            if printer.type == PrinterType.NETWORK:
                success = self._send_to_network_printer(printer, output)
            elif printer.type == PrinterType.USB:
                success = self._send_to_usb_printer(printer, output)
            else:
                return {"success": False, "error": f"Unsupported printer type"}

            if success:
                logger.info(f"Cash drawer opened via {printer.name}")
                return {
                    "success": True,
                    "message": f"Cash drawer opened on {printer.name}",
                    "printer_id": printer_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to open cash drawer on {printer.name}",
                }
        except Exception as e:
            logger.error(f"Error opening cash drawer: {e}")
            return {"success": False, "error": str(e)}

    def cut_paper(
        self, printer_id: Optional[str] = None, partial: bool = False
    ) -> Dict[str, Any]:
        """
        Cut paper on thermal printer

        Args:
            printer_id: ID of printer
            partial: If True, partial cut; if False, full cut
        """
        try:
            if not printer_id:
                default_printer = next(
                    (p for p in self.printers.values() if p.is_default), None
                )
                if not default_printer:
                    return {"success": False, "error": "No printer configured"}
                printer_id = default_printer.id

            printer = self.get_printer(printer_id)
            if not printer:
                return {"success": False, "error": f"Printer {printer_id} not found"}

            output = (
                ESCPOSCommands.PAPER_CUT_PARTIAL
                if partial
                else ESCPOSCommands.PAPER_CUT_FULL
            )

            if printer.type == PrinterType.NETWORK:
                success = self._send_to_network_printer(printer, output)
            elif printer.type == PrinterType.USB:
                success = self._send_to_usb_printer(printer, output)
            else:
                return {"success": False, "error": f"Unsupported printer type"}

            cut_type = "partial" if partial else "full"
            if success:
                logger.info(f"Paper cut ({cut_type}) executed on {printer.name}")
                return {
                    "success": True,
                    "message": f"Paper {cut_type} cut on {printer.name}",
                    "printer_id": printer_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to cut paper on {printer.name}",
                }
        except Exception as e:
            logger.error(f"Error cutting paper: {e}")
            return {"success": False, "error": str(e)}

    def test_print(self, printer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Print test page to verify printer connection

        Args:
            printer_id: ID of printer to test
        """
        try:
            if not printer_id:
                default_printer = next(
                    (p for p in self.printers.values() if p.is_default), None
                )
                if not default_printer:
                    return {"success": False, "error": "No printer configured"}
                printer_id = default_printer.id

            printer = self.get_printer(printer_id)
            if not printer:
                return {"success": False, "error": f"Printer {printer_id} not found"}

            # Build test page
            output = ESCPOSCommands.INIT
            output += ESCPOSCommands.ALIGN_CENTER
            output += ESCPOSCommands.BOLD_ON
            output += "PRINTER TEST PAGE\n".encode("utf-8")
            output += ESCPOSCommands.BOLD_OFF
            output += ESCPOSCommands.ALIGN_LEFT
            output += f"Printer: {printer.name}\n".encode("utf-8")
            output += f"Type: {printer.type.value}\n".encode("utf-8")
            output += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n".encode(
                "utf-8"
            )
            output += "\n".encode("utf-8")
            output += "If you see this, printer is working!\n".encode("utf-8")
            output += "\n".encode("utf-8")
            output += ESCPOSCommands.PAPER_CUT_FULL

            if printer.type == PrinterType.NETWORK:
                success = self._send_to_network_printer(printer, output)
            elif printer.type == PrinterType.USB:
                success = self._send_to_usb_printer(printer, output)
            else:
                return {"success": False, "error": f"Unsupported printer type"}

            if success:
                logger.info(f"Test print sent to {printer.name}")
                return {
                    "success": True,
                    "message": f"Test page printed on {printer.name}",
                    "printer_id": printer_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to print test page on {printer.name}",
                }
        except Exception as e:
            logger.error(f"Error test printing: {e}")
            return {"success": False, "error": str(e)}


# Global printer service instance
printer_service = PrinterService()
