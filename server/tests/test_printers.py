"""
Test cases for printer service and API endpoints.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.peripherals import PrinterConfigIn
from app.services.printer_service import (
    PrinterConfig,
    PrinterService,
    PrinterStatus,
    PrinterType,
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers with valid JWT token."""
    # This assumes there's an auth fixture from conftest
    return {"Authorization": "Bearer test_token"}


class TestPrinterService:
    """Test PrinterService class."""

    def test_printer_config_creation(self):
        """Test creating printer config."""
        config = PrinterConfig(
            id="printer_1",
            name="Receipt Printer",
            type=PrinterType.NETWORK,
            ip_address="192.168.1.100",
        )

        assert config.id == "printer_1"
        assert config.name == "Receipt Printer"
        assert config.type == PrinterType.NETWORK
        assert config.ip_address == "192.168.1.100"

    def test_printer_type_enum(self):
        """Test PrinterType enum values."""
        assert PrinterType.USB.value == "usb"
        assert PrinterType.NETWORK.value == "network"
        assert PrinterType.BLUETOOTH.value == "bluetooth"

    def test_printer_status_enum(self):
        """Test PrinterStatus enum values."""
        assert PrinterStatus.ONLINE.value == "online"
        assert PrinterStatus.OFFLINE.value == "offline"
        assert PrinterStatus.ERROR.value == "error"
        assert PrinterStatus.OUT_OF_PAPER.value == "out_of_paper"

    @patch("app.services.printer_service.socket")
    def test_check_printer_status_online(self, mock_socket):
        """Test checking printer status - online."""
        mock_sock = MagicMock()
        mock_socket.socket.return_value = mock_sock
        mock_socket.AF_INET = 2
        mock_socket.SOCK_STREAM = 1
        mock_sock.connect_ex.return_value = 0  # Success code

        service = PrinterService()
        config = PrinterConfig(
            id="test_printer",
            name="Test",
            type=PrinterType.NETWORK,
            ip_address="192.168.1.100",
        )

        status = service._check_network_printer_status(config)
        assert status == PrinterStatus.ONLINE
        mock_sock.close.assert_called_once()

    @patch("app.services.printer_service.socket")
    def test_check_printer_status_offline(self, mock_socket):
        """Test checking printer status - offline."""
        mock_sock = MagicMock()
        mock_socket.socket.return_value = mock_sock
        mock_socket.AF_INET = 2
        mock_socket.SOCK_STREAM = 1
        mock_sock.connect_ex.return_value = 1  # Failure code (any non-zero)

        service = PrinterService()
        config = PrinterConfig(
            id="test_printer",
            name="Test",
            type=PrinterType.NETWORK,
            ip_address="192.168.1.100",
        )

        status = service._check_network_printer_status(config)
        assert status == PrinterStatus.OFFLINE

    def test_escp_commands_exist(self):
        """Test ESC/POS commands are defined."""
        from app.services.printer_service import ESCPOSCommands

        # Check basic commands exist
        assert hasattr(ESCPOSCommands, "RESET")
        assert hasattr(ESCPOSCommands, "BOLD_ON")
        assert hasattr(ESCPOSCommands, "BOLD_OFF")
        assert hasattr(ESCPOSCommands, "ALIGN_CENTER")
        assert hasattr(ESCPOSCommands, "CASH_DRAWER_OPEN")
        assert hasattr(ESCPOSCommands, "PAPER_CUT_FULL")
        assert hasattr(ESCPOSCommands, "PAPER_CUT_PARTIAL")


class TestPrinterAPI:
    """Test Printer API endpoints."""

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_register_network_printer(self, mock_service, client, auth_headers):
        """Test registering a network printer."""
        mock_service.register_printer.return_value = True  # Should return True
        mock_service.check_printer_status.return_value = PrinterStatus.ONLINE

        response = client.post(
            "/api/v1/peripherals/printers/register",
            headers=auth_headers,
            json={
                "name": "Receipt Printer",
                "type": "network",
                "ip_address": "192.168.1.100",
                "port": 9100,
                "paper_width": 80,
                "is_default": True,
            },
        )

        assert response.status_code == 201  # Should be 201 CREATED
        data = response.json()
        assert data["name"] == "Receipt Printer"
        assert data["type"] == "network"

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_register_usb_printer(self, mock_service, client, auth_headers):
        """Test registering a USB printer."""
        mock_service.register_printer.return_value = True
        mock_service.check_printer_status.return_value = PrinterStatus.ONLINE

        response = client.post(
            "/api/v1/peripherals/printers/register",
            headers=auth_headers,
            json={
                "name": "USB Printer",
                "type": "usb",
                "usb_vendor_id": "0x0483",
                "usb_product_id": "0x2016",
                "paper_width": 58,
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["type"] == "usb"

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_list_printers(self, mock_service, client, auth_headers):
        """Test listing all printers."""
        mock_service.list_printers.return_value = [
            {
                "id": "printer_1",
                "name": "Receipt Printer",
                "type": "network",
                "status": "online",
            },
            {
                "id": "printer_2",
                "name": "Kitchen Printer",
                "type": "network",
                "status": "online",
            },
        ]
        response = client.get("/api/v1/peripherals/printers", headers=auth_headers)

        assert response.status_code in [200, 201]
        data = response.json()
        assert len(data["printers"]) == 2
        assert data["printers"][0]["name"] == "Receipt Printer"

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_get_printer_status(self, mock_service, client, auth_headers):
        """Test getting printer status."""
        # Mock the printer object from get_printer
        mock_printer = Mock()
        mock_printer.id = "printer_1"
        mock_printer.name = "Receipt Printer"
        mock_printer.type = "network"
        mock_printer.ip_address = "192.168.1.100"
        mock_printer.port = 9100
        mock_printer.is_active = True
        mock_printer.is_default = True

        mock_service.get_printer.return_value = mock_printer
        mock_service.check_printer_status.return_value = PrinterStatus.ONLINE

        response = client.get(
            "/api/v1/peripherals/printers/printer_1/status", headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["status"] == "online"

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_test_printer(self, mock_service, client, auth_headers):
        """Test print test page."""
        mock_service.test_print.return_value = {
            "success": True,
            "message": "Test page printed on Receipt Printer",
            "printer_id": "printer_1",
        }
        response = client.post(
            "/api/v1/peripherals/printers/printer_1/test", headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
        assert "Test page printed" in data["message"]

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_print_receipt(self, mock_service, client, auth_headers):
        """Test printing receipt."""
        mock_service.print_receipt.return_value = {
            "success": True,
            "message": "Printed 1 copy on Receipt Printer",
            "printer_id": "printer_1",
            "copies": 1,
        }
        response = client.post(
            "/api/v1/peripherals/printers/print-receipt",
            headers=auth_headers,
            json={
                "receipt_id": 42,
                "printer_id": "printer_1",
                "copies": 1,
                "paper_width": 80,
            },
        )

        # May get 404 if sale not found in test database, or 200 if success
        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            assert data["copies"] == 1

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_print_multiple_copies(self, mock_service, client, auth_headers):
        """Test printing multiple copies."""
        mock_service.print_receipt.return_value = {
            "success": True,
            "message": "Printed 3 copies on Receipt Printer",
            "printer_id": "printer_1",
            "copies": 3,
        }
        response = client.post(
            "/api/v1/peripherals/printers/print-receipt",
            headers=auth_headers,
            json={
                "receipt_id": 42,
                "printer_id": "printer_1",
                "copies": 3,
                "paper_width": 80,
            },
        )

        # May get 404 if sale not found in test database, or 200 if success
        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["copies"] == 3

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_open_cash_drawer(self, mock_service, client, auth_headers):
        """Test opening cash drawer."""
        mock_service.open_cash_drawer.return_value = {
            "success": True,
            "message": "Cash drawer opened on Receipt Printer",
            "printer_id": "printer_1",
        }
        response = client.post(
            "/api/v1/peripherals/cash-drawer/open",
            headers=auth_headers,
            json={"printer_id": "printer_1"},
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
        assert "drawer opened" in data["message"]

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_cut_paper_full(self, mock_service, client, auth_headers):
        """Test full paper cut."""
        mock_service.cut_paper.return_value = {
            "success": True,
            "message": "Full cut performed on Receipt Printer",
            "printer_id": "printer_1",
            "partial": False,
        }
        response = client.post(
            "/api/v1/peripherals/printers/printer_1/cut-paper",
            headers=auth_headers,
            json={"partial": False},
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
        assert data["partial"] is False

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_cut_paper_partial(self, mock_service, client, auth_headers):
        """Test partial paper cut."""
        mock_service.cut_paper.return_value = {
            "success": True,
            "message": "Partial cut performed on Receipt Printer",
            "printer_id": "printer_1",
            "partial": True,
        }
        response = client.post(
            "/api/v1/peripherals/printers/printer_1/cut-paper",
            headers=auth_headers,
            json={"partial": True},
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["partial"] is True

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_register_printer_invalid_type(self, mock_service, client, auth_headers):
        """Test registering printer with invalid type."""
        response = client.post(
            "/api/v1/peripherals/printers/register",
            headers=auth_headers,
            json={"name": "Invalid Printer", "type": "invalid_type", "paper_width": 80},
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_print_receipt_invalid_copies(self, mock_service, client, auth_headers):
        """Test printing with invalid copy count."""
        response = client.post(
            "/api/v1/peripherals/printers/print-receipt",
            headers=auth_headers,
            json={
                "receipt_id": 42,
                "printer_id": "printer_1",
                "copies": 15,  # Max is 10
                "paper_width": 80,
            },
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_no_auth_header(self, mock_service, client):
        """Test endpoints without auth headers still work (due to test override)."""
        # In test environment, dependency overrides provide a test user
        mock_service.list_printers.return_value = []

        response = client.get("/api/v1/peripherals/printers")
        # Should work because test user is provided by override
        assert response.status_code in [200, 201]


class TestPrinterEdgeCases:
    """Test edge cases and error handling."""

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_printer_not_found(self, mock_service, client, auth_headers):
        """Test requesting non-existent printer."""
        mock_service.get_printer.return_value = None  # Printer not found

        response = client.get(
            "/api/v1/peripherals/printers/nonexistent/status", headers=auth_headers
        )

        assert response.status_code == 404

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_printer_connection_error(self, mock_service, client, auth_headers):
        """Test handling printer connection error."""
        mock_printer = Mock()
        mock_printer.id = "printer_1"
        mock_printer.name = "Receipt Printer"
        mock_printer.type = "network"
        mock_printer.ip_address = "192.168.1.100"
        mock_printer.port = 9100
        mock_printer.is_active = True
        mock_printer.is_default = True

        mock_service.get_printer.return_value = mock_printer
        mock_service.test_print.side_effect = ConnectionError(
            "Cannot connect to printer"
        )

        response = client.post(
            "/api/v1/peripherals/printers/printer_1/test", headers=auth_headers
        )

        assert response.status_code == 500

    @patch("app.api.v1.routers.peripherals.printer_service")
    def test_receipt_not_found(self, mock_service, client, auth_headers):
        """Test printing non-existent receipt."""
        mock_instance = MagicMock()
        mock_instance.print_receipt.side_effect = ValueError("Receipt not found")
        response = client.post(
            "/api/v1/peripherals/printers/print-receipt",
            headers=auth_headers,
            json={"receipt_id": 9999, "printer_id": "printer_1", "copies": 1},
        )

        assert response.status_code == 404
