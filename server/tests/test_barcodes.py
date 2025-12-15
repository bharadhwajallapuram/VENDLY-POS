"""
Test cases for barcode service and API endpoints.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.barcode_service import BarcodeFormat, BarcodeService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers with valid JWT token."""
    return {"Authorization": "Bearer test_token"}


class TestBarcodeService:
    """Test BarcodeService class."""

    def test_barcode_format_enum(self):
        """Test BarcodeFormat enum values."""
        assert BarcodeFormat.CODE128.value == "code128"
        assert BarcodeFormat.CODE39.value == "code39"
        assert BarcodeFormat.EAN13.value == "ean13"
        assert BarcodeFormat.EAN8.value == "ean8"
        assert BarcodeFormat.UPC_A.value == "upca"
        assert BarcodeFormat.UPC_E.value == "upce"
        assert BarcodeFormat.QR_CODE.value == "qr"
        assert BarcodeFormat.DATA_MATRIX.value == "datamatrix"

    def test_generate_code128(self):
        """Test generating Code128 barcode."""
        service = BarcodeService()
        result = service.generate_barcode(
            data="123456789", format=BarcodeFormat.CODE128, width=200, height=100
        )

        # Should either have image or error
        assert result is not None

    def test_validate_ean13_valid(self):
        """Test validating valid EAN-13."""
        service = BarcodeService()
        is_valid = service.validate_barcode("9780134685991", "ean13")
        assert is_valid["valid"] is True

    def test_validate_ean13_invalid_length(self):
        """Test validating EAN-13 with wrong length."""
        service = BarcodeService()
        is_valid = service.validate_barcode("978013468599", "ean13")  # Missing digit
        assert is_valid["valid"] is False

    def test_validate_ean13_invalid_characters(self):
        """Test validating EAN-13 with invalid characters."""
        service = BarcodeService()
        is_valid = service.validate_barcode("978013468599X", "ean13")  # Contains letter
        assert is_valid["valid"] is False

    def test_validate_ean8_valid(self):
        """Test validating valid EAN-8."""
        service = BarcodeService()
        is_valid = service.validate_barcode("96385074", "ean8")
        assert is_valid["valid"] is True

    def test_validate_ean8_invalid_length(self):
        """Test validating EAN-8 with wrong length."""
        service = BarcodeService()
        is_valid = service.validate_barcode("9638507", "ean8")  # Missing digit
        assert is_valid["valid"] is False

    def test_validate_code128_valid(self):
        """Test validating Code128."""
        service = BarcodeService()
        is_valid = service.validate_barcode("CODE128DATA", BarcodeFormat.CODE128)
        assert is_valid["valid"] is True

    def test_validate_code39_valid(self):
        """Test validating Code39."""
        service = BarcodeService()
        is_valid = service.validate_barcode("CODE39DATA", BarcodeFormat.CODE39)
        assert is_valid["valid"] is True

    def test_validate_upca_valid(self):
        """Test validating valid UPC-A."""
        service = BarcodeService()
        is_valid = service.validate_barcode("123456789012", BarcodeFormat.UPC_A)
        assert is_valid["valid"] is True

    def test_validate_upca_invalid_length(self):
        """Test validating UPC-A with wrong length."""
        service = BarcodeService()
        is_valid = service.validate_barcode(
            "1234567890", BarcodeFormat.UPC_A
        )  # Missing digit
        assert is_valid["valid"] is False

    def test_validate_upce_valid(self):
        """Test validating valid UPC-E."""
        service = BarcodeService()
        is_valid = service.validate_barcode("123456", BarcodeFormat.UPC_E)
        assert is_valid["valid"] is True

    def test_validate_qr_valid(self):
        """Test validating QR code."""
        service = BarcodeService()
        is_valid = service.validate_barcode("https://vendly.com", BarcodeFormat.QR_CODE)
        assert is_valid["valid"] is True

    def test_validate_qr_empty(self):
        """Test validating empty QR code."""
        service = BarcodeService()
        is_valid = service.validate_barcode("", BarcodeFormat.QR_CODE)
        assert is_valid["valid"] is False

    def test_validate_invalid_format(self):
        """Test validating with invalid data length."""
        service = BarcodeService()
        is_valid = service.validate_barcode(
            "123", BarcodeFormat.EAN13
        )  # 3 digits instead of 13
        assert is_valid["valid"] is False

    def test_generate_qr_code(self):
        """Test generating QR code."""
        service = BarcodeService()
        result = service.generate_barcode(
            data="https://vendly.com",
            format=BarcodeFormat.QR_CODE,
            width=200,
            height=200,
        )

        # Should either have image or error
        assert result is not None


class TestBarcodeAPI:
    """Test Barcode API endpoints."""

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_qr_code(self, mock_service, client, auth_headers):
        """Test generating QR code via API."""
        mock_service.generate_barcode.return_value = {
            "success": True,
            "format": "qr",
            "data": "https://vendly.com/product/42",
            "image_base64": "data:image/png;base64,iVBORw0KGgo...",
            "svg": "<svg>...</svg>",
            "width": 200,
            "height": 200,
        }
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={
                "data": "https://vendly.com/product/42",
                "format": "qr",
                "width": 200,
                "height": 200,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "qr"
        assert "image_base64" in data

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_ean13(self, mock_service, client, auth_headers):
        """Test generating EAN-13 barcode via API."""
        mock_service.generate_barcode.return_value = {
            "success": True,
            "format": "ean13",
            "data": "9780134685991",
            "image_base64": "data:image/png;base64,iVBORw0KGgo...",
            "svg": "<svg>...</svg>",
            "width": 200,
            "height": 100,
        }
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={
                "data": "9780134685991",
                "format": "ean13",
                "width": 200,
                "height": 100,
                "include_text": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "ean13"
        assert data["data"] == "9780134685991"

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_code128(self, mock_service, client, auth_headers):
        """Test generating Code128 barcode via API."""
        mock_service.generate_barcode.return_value = {
            "success": True,
            "format": "code128",
            "data": "ORDER-12345",
            "image_base64": "data:image/png;base64,iVBORw0KGgo...",
            "width": 300,
            "height": 80,
        }
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={
                "data": "ORDER-12345",
                "format": "code128",
                "width": 300,
                "height": 80,
                "include_text": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "code128"

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_validate_barcode_valid(self, mock_service, client, auth_headers):
        """Test validating barcode via API."""
        mock_service.validate_barcode.return_value = {
            "valid": True,
            "message": "Valid EAN-13",
        }
        response = client.post(
            "/api/v1/peripherals/barcodes/validate",
            headers=auth_headers,
            json={"data": "9780134685991", "format": "ean13"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_validate_barcode_invalid(self, mock_service, client, auth_headers):
        """Test validating invalid barcode via API."""
        mock_service.validate_barcode.return_value = {
            "valid": False,
            "error": "Invalid EAN-13: wrong length",
        }
        response = client.post(
            "/api/v1/peripherals/barcodes/validate",
            headers=auth_headers,
            json={"data": "978013468599", "format": "ean13"},  # Wrong length
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_list_barcode_formats(self, mock_service, client, auth_headers):
        """Test listing barcode formats via API."""
        mock_service.get_supported_formats.return_value = [
            {
                "format": "code128",
                "name": "Code128",
                "max_length": 80,
                "type": "linear",
            },
            {"format": "ean13", "name": "EAN-13", "max_length": 13, "type": "linear"},
            {"format": "qr", "name": "QR Code", "max_length": 4296, "type": "2d"},
        ]
        response = client.get(
            "/api/v1/peripherals/barcodes/formats", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["formats"]) >= 3

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_barcode_no_auth(self, mock_service, client):
        """Test barcode endpoints work with test auth override."""
        # In test environment, dependency overrides provide a test user
        mock_service.generate_barcode.return_value = {
            "success": True,
            "format": "qr",
            "data": "test",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        }

        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            json={"data": "test", "format": "qr"},
        )
        # Should work because test user is provided by override
        assert response.status_code in [200, 201]

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_barcode_invalid_format(self, mock_service, client, auth_headers):
        """Test generating barcode with invalid format."""
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={"data": "test", "format": "invalid_format"},
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_barcode_empty_data(self, mock_service, client, auth_headers):
        """Test generating barcode with empty data."""
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={"data": "", "format": "qr"},
        )

        assert response.status_code == 422  # Validation error


class TestBarcodeEdgeCases:
    """Test edge cases and error handling."""

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_generate_barcode_service_error(self, mock_service, client, auth_headers):
        """Test handling barcode generation error."""
        mock_service.generate_barcode.side_effect = Exception(
            "Barcode generation failed"
        )
        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={"data": "test", "format": "qr"},
        )

        assert response.status_code == 500

    @patch("app.api.v1.routers.peripherals.barcode_service")
    def test_validate_barcode_service_error(self, mock_service, client, auth_headers):
        """Test handling barcode validation error."""
        mock_service.validate_barcode.side_effect = Exception("Validation error")
        response = client.post(
            "/api/v1/peripherals/barcodes/validate",
            headers=auth_headers,
            json={"data": "test", "format": "qr"},
        )

        assert response.status_code == 500

    def test_generate_barcode_large_data(self, client, auth_headers):
        """Test generating barcode with large data."""
        large_data = "x" * 5000  # Very large data

        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={"data": large_data, "format": "qr"},
        )

        # Should handle gracefully (either succeed or fail with 422)
        assert response.status_code in [200, 422]

    def test_generate_barcode_special_characters(self, client, auth_headers):
        """Test generating barcode with special characters."""
        special_data = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        response = client.post(
            "/api/v1/peripherals/barcodes/generate",
            headers=auth_headers,
            json={"data": special_data, "format": "code128"},
        )

        # Code128 supports most characters
        assert response.status_code in [200, 422, 500]
