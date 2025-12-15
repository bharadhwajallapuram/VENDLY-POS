"""
Vendly POS - Barcode Service
Generates barcodes (Code128, UPC, EAN, QR Code) for products
"""

import io
import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BarcodeFormat(str, Enum):
    """Supported barcode formats"""

    CODE128 = "code128"
    CODE39 = "code39"
    EAN13 = "ean13"
    EAN8 = "ean8"
    UPC_A = "upca"
    UPC_E = "upce"
    QR_CODE = "qr"
    DATA_MATRIX = "datamatrix"


class BarcodeService:
    """Service for generating barcodes"""

    @staticmethod
    def generate_barcode(
        data: str,
        format: BarcodeFormat = BarcodeFormat.CODE128,
        width: int = 200,
        height: int = 100,
        include_text: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate barcode image

        Args:
            data: Data to encode
            format: Barcode format
            width: Image width in pixels
            height: Image height in pixels
            include_text: Include barcode text below image

        Returns:
            Dict with image data (base64), SVG, or error
        """
        try:
            if format == BarcodeFormat.QR_CODE:
                return BarcodeService._generate_qr_code(
                    data, width, height, include_text
                )
            else:
                return BarcodeService._generate_linear_barcode(
                    data, format, width, height, include_text
                )
        except Exception as e:
            logger.error(f"Error generating barcode: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _generate_linear_barcode(
        data: str, format: BarcodeFormat, width: int, height: int, include_text: bool
    ) -> Dict[str, Any]:
        """Generate linear barcode (Code128, UPC, etc.)"""
        try:
            import base64

            from barcode import get_barcode_class
            from barcode.writer import ImageWriter, SVGWriter

            # Map format to barcode library format
            format_map = {
                BarcodeFormat.CODE128: "code128",
                BarcodeFormat.CODE39: "code39",
                BarcodeFormat.EAN13: "ean13",
                BarcodeFormat.EAN8: "ean8",
                BarcodeFormat.UPC_A: "upca",
                BarcodeFormat.UPC_E: "upce",
            }

            barcode_format = format_map.get(format, "code128")

            # Generate barcode
            BarcodeClass = get_barcode_class(barcode_format)
            barcode = BarcodeClass(data, writer=ImageWriter())

            # Generate image
            image_buffer = io.BytesIO()
            barcode.write(
                image_buffer,
                options={
                    "width": width,
                    "height": height,
                    "font_size": 14 if include_text else 0,
                },
            )
            image_buffer.seek(0)

            # Convert to base64
            import base64

            image_data = base64.b64encode(image_buffer.getvalue()).decode("utf-8")

            # Also generate SVG for web display
            svg_buffer = io.BytesIO()
            barcode_svg = BarcodeClass(data, writer=SVGWriter())
            barcode_svg.write(
                svg_buffer,
                options={
                    "width": width,
                    "height": height,
                    "font_size": 14 if include_text else 0,
                },
            )
            svg_buffer.seek(0)
            svg_data = svg_buffer.getvalue().decode("utf-8")

            return {
                "success": True,
                "format": format.value,
                "data": data,
                "image_base64": f"data:image/png;base64,{image_data}",
                "svg": svg_data,
                "width": width,
                "height": height,
            }
        except ImportError:
            return {
                "success": False,
                "error": "python-barcode library not installed. Run: pip install python-barcode pillow",
            }

    @staticmethod
    def _generate_qr_code(
        data: str, width: int, height: int, include_text: bool
    ) -> Dict[str, Any]:
        """Generate QR code"""
        try:
            import base64

            import qrcode

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Resize if needed
            if width != img.width or height != img.height:
                img = img.resize((width, height))

            # Convert to base64
            image_buffer = io.BytesIO()
            img.save(image_buffer, format="PNG")
            image_buffer.seek(0)
            image_data = base64.b64encode(image_buffer.getvalue()).decode("utf-8")

            # Generate SVG version
            try:
                import qrcode.image.svg

                factory = qrcode.image.svg.SvgPathImage
                qr_svg = qrcode.QRCode(image_factory=factory)
                qr_svg.add_data(data)
                qr_svg.make(fit=True)

                svg_buffer = io.BytesIO()
                qr_svg.make_image().save(svg_buffer)
                svg_buffer.seek(0)
                svg_data = svg_buffer.getvalue().decode("utf-8")
            except Exception:
                svg_data = None

            result = {
                "success": True,
                "format": "qr",
                "data": data,
                "image_base64": f"data:image/png;base64,{image_data}",
                "width": width,
                "height": height,
            }

            if svg_data:
                result["svg"] = svg_data

            return result
        except ImportError:
            return {
                "success": False,
                "error": "qrcode library not installed. Run: pip install qrcode[pil]",
            }

    @staticmethod
    def validate_barcode(
        data: str, format: BarcodeFormat = BarcodeFormat.CODE128
    ) -> Dict[str, Any]:
        """
        Validate barcode data for format

        Args:
            data: Data to validate
            format: Barcode format

        Returns:
            Dict with validation result
        """
        try:
            # Handle string format input (convert to enum)
            if isinstance(format, str):
                try:
                    format = BarcodeFormat(format)
                except ValueError:
                    return {
                        "valid": False,
                        "error": f"Unknown barcode format: {format}",
                    }

            if format == BarcodeFormat.EAN13:
                return BarcodeService._validate_ean13(data)
            elif format == BarcodeFormat.EAN8:
                return BarcodeService._validate_ean8(data)
            elif format == BarcodeFormat.UPC_A:
                return BarcodeService._validate_upca(data)
            elif format == BarcodeFormat.UPC_E:
                return BarcodeService._validate_upce(data)
            elif format == BarcodeFormat.CODE128:
                return BarcodeService._validate_code128(data)
            elif format == BarcodeFormat.CODE39:
                return BarcodeService._validate_code39(data)
            elif format == BarcodeFormat.QR_CODE:
                return BarcodeService._validate_qr_code(data)
            elif format == BarcodeFormat.DATAMATRIX:
                return {
                    "valid": True,
                    "message": "DataMatrix validation not implemented",
                }
            else:
                return {"valid": False, "error": f"Unsupported format: {format}"}
        except Exception as e:
            logger.error(f"Error validating barcode: {e}")
            return {"valid": False, "error": str(e)}

    @staticmethod
    def _validate_qr_code(data: str) -> Dict[str, Any]:
        """Validate QR code data"""
        if not data or len(data) < 1:
            return {"valid": False, "error": "QR code data cannot be empty"}
        return {"valid": True, "message": "Valid QR code data"}

    @staticmethod
    def _validate_ean13(data: str) -> Dict[str, Any]:
        """Validate EAN-13"""
        if not data.isdigit() or len(data) != 13:
            return {"valid": False, "error": "EAN-13 must be 13 digits"}
        return {"valid": True, "message": "Valid EAN-13"}

    @staticmethod
    def _validate_ean8(data: str) -> Dict[str, Any]:
        """Validate EAN-8"""
        if not data.isdigit() or len(data) != 8:
            return {"valid": False, "error": "EAN-8 must be 8 digits"}
        return {"valid": True, "message": "Valid EAN-8"}

    @staticmethod
    def _validate_upca(data: str) -> Dict[str, Any]:
        """Validate UPC-A"""
        if not data.isdigit() or len(data) != 12:
            return {"valid": False, "error": "UPC-A must be 12 digits"}
        return {"valid": True, "message": "Valid UPC-A"}

    @staticmethod
    def _validate_upce(data: str) -> Dict[str, Any]:
        """Validate UPC-E"""
        if not data.isdigit() or len(data) != 6:
            return {"valid": False, "error": "UPC-E must be 6 digits"}
        return {"valid": True, "message": "Valid UPC-E"}

    @staticmethod
    def _validate_code128(data: str) -> Dict[str, Any]:
        """Validate Code128"""
        # Code128 accepts most printable ASCII characters
        if len(data) < 1 or len(data) > 255:
            return {"valid": False, "error": "Code128 must be 1-255 characters"}
        return {"valid": True, "message": "Valid Code128"}

    @staticmethod
    def _validate_code39(data: str) -> Dict[str, Any]:
        """Validate Code39"""
        # Code39 accepts alphanumeric and some special chars
        valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -.$/+%")
        if not all(c in valid_chars for c in data.upper()):
            return {"valid": False, "error": "Code39 contains invalid characters"}
        return {"valid": True, "message": "Valid Code39"}


# Global barcode service instance
barcode_service = BarcodeService()
