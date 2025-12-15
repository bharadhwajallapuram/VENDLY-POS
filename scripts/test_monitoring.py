#!/usr/bin/env python3
"""
Vendly POS - Monitoring & Backup Integration Tests
===================================================
Validate that error tracking, health checks, and backups work correctly
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MonitoringTests:
    """Test suite for monitoring systems"""

    def __init__(self, base_url: str = "http://localhost:8000", db_url: str = ""):
        self.base_url = base_url
        self.db_url = db_url
        self.passed = 0
        self.failed = 0

    def test_health_endpoint(self, endpoint: str, expected_status: int = 200):
        """Test a health endpoint"""
        url = f"{self.base_url}/api/v1{endpoint}"
        test_name = f"Health Endpoint: {endpoint}"

        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=10,
            )

            status = int(result.stdout.strip())
            if status == expected_status:
                logger.info(f"✓ {test_name}: {status}")
                self.passed += 1
                return True
            else:
                logger.error(
                    f"✗ {test_name}: Expected {expected_status}, got {status}"
                )
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"✗ {test_name}: {e}")
            self.failed += 1
            return False

    def test_detailed_health(self):
        """Test detailed health endpoint and check response format"""
        test_name = "Detailed Health Check"
        url = f"{self.base_url}/api/v1/health/detailed"

        try:
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                timeout=10,
            )

            data = json.loads(result.stdout)

            # Verify response structure
            required_fields = ["status", "timestamp", "services"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"✗ {test_name}: Missing field '{field}'")
                    self.failed += 1
                    return False

            # Check services
            if not isinstance(data["services"], list):
                logger.error(f"✗ {test_name}: 'services' is not a list")
                self.failed += 1
                return False

            # Check service structure
            for service in data["services"]:
                required_service_fields = ["name", "status", "response_time_ms"]
                for field in required_service_fields:
                    if field not in service:
                        logger.error(
                            f"✗ {test_name}: Service '{service.get('name')}' missing '{field}'"
                        )
                        self.failed += 1
                        return False

            logger.info(
                f"✓ {test_name}: All {len(data['services'])} services present"
            )
            self.passed += 1
            return True

        except json.JSONDecodeError:
            logger.error(f"✗ {test_name}: Invalid JSON response")
            self.failed += 1
            return False
        except Exception as e:
            logger.error(f"✗ {test_name}: {e}")
            self.failed += 1
            return False

    def test_sentry_import(self):
        """Test that Sentry is properly installed"""
        test_name = "Sentry Module Import"

        try:
            import sentry_sdk

            logger.info(f"✓ {test_name}: sentry-sdk {sentry_sdk.__version__}")
            self.passed += 1
            return True
        except ImportError:
            logger.error(f"✗ {test_name}: sentry-sdk not installed")
            logger.info("  Run: pip install sentry-sdk")
            self.failed += 1
            return False

    def test_database_backup_script(self):
        """Test that backup script exists and is executable"""
        test_name = "Backup Script Availability"
        script_path = Path("scripts/backup_manager.py")

        if not script_path.exists():
            logger.error(f"✗ {test_name}: {script_path} not found")
            self.failed += 1
            return False

        if not script_path.is_file():
            logger.error(f"✗ {test_name}: {script_path} is not a file")
            self.failed += 1
            return False

        logger.info(f"✓ {test_name}: Found at {script_path.absolute()}")
        self.passed += 1
        return True

    def test_backup_help(self):
        """Test backup script help output"""
        test_name = "Backup Script Help"

        try:
            result = subprocess.run(
                ["python", "scripts/backup_manager.py", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "usage" in result.stdout.lower():
                logger.info(f"✓ {test_name}: Help output valid")
                self.passed += 1
                return True
            else:
                logger.error(f"✗ {test_name}: Help output failed")
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"✗ {test_name}: {e}")
            self.failed += 1
            return False

    def test_error_tracking_file(self):
        """Test that error tracking module exists"""
        test_name = "Error Tracking Module"
        module_path = Path("server/app/core/error_tracking.py")

        if not module_path.exists():
            logger.error(f"✗ {test_name}: {module_path} not found")
            self.failed += 1
            return False

        logger.info(f"✓ {test_name}: Found at {module_path.absolute()}")
        self.passed += 1
        return True

    def test_health_check_service(self):
        """Test that health check service exists"""
        test_name = "Health Check Service"
        service_path = Path("server/app/services/health_check.py")

        if not service_path.exists():
            logger.error(f"✗ {test_name}: {service_path} not found")
            self.failed += 1
            return False

        logger.info(f"✓ {test_name}: Found at {service_path.absolute()}")
        self.passed += 1
        return True

    def test_kubernetes_deployment(self):
        """Test that Kubernetes deployment has health probes"""
        test_name = "Kubernetes Deployment Probes"
        deployment_path = Path("k8s/deployment.yaml")

        if not deployment_path.exists():
            logger.error(f"✗ {test_name}: {deployment_path} not found")
            self.failed += 1
            return False

        content = deployment_path.read_text()

        probes = ["livenessProbe", "readinessProbe", "startupProbe"]
        missing = [p for p in probes if p not in content]

        if missing:
            logger.error(f"✗ {test_name}: Missing probes: {missing}")
            self.failed += 1
            return False

        logger.info(f"✓ {test_name}: All probes configured")
        self.passed += 1
        return True

    def test_dockerfile_healthcheck(self):
        """Test that Dockerfile has HEALTHCHECK"""
        test_name = "Docker HEALTHCHECK"
        dockerfile_path = Path("Dockerfile")

        if not dockerfile_path.exists():
            logger.error(f"✗ {test_name}: Dockerfile not found")
            self.failed += 1
            return False

        content = dockerfile_path.read_text()

        if "HEALTHCHECK" not in content:
            logger.error(f"✗ {test_name}: HEALTHCHECK not found in Dockerfile")
            self.failed += 1
            return False

        if "/health/live" in content:
            logger.info(f"✓ {test_name}: HEALTHCHECK configured with /health/live")
            self.passed += 1
            return True
        else:
            logger.warning(f"⚠ {test_name}: HEALTHCHECK uses different endpoint")
            self.passed += 1
            return True

    def test_documentation(self):
        """Test that documentation files exist"""
        test_name = "Documentation"
        docs = [
            Path("docs/MONITORING_SETUP.md"),
            Path("IMPLEMENTATION_SUMMARY.md"),
            Path("QUICK_REFERENCE.md"),
        ]

        missing = [d for d in docs if not d.exists()]

        if missing:
            logger.warning(f"⚠ {test_name}: Missing docs: {missing}")
            self.failed += 1
            return False

        logger.info(f"✓ {test_name}: All documentation present ({len(docs)} files)")
        self.passed += 1
        return True

    def run_all_tests(self):
        """Run all tests"""
        logger.info("=" * 70)
        logger.info("VENDLY POS - MONITORING INTEGRATION TEST SUITE")
        logger.info("=" * 70)

        print("\n📋 Configuration Tests")
        print("-" * 70)
        self.test_error_tracking_file()
        self.test_health_check_service()
        self.test_database_backup_script()
        self.test_documentation()
        self.test_kubernetes_deployment()
        self.test_dockerfile_healthcheck()

        print("\n🔧 Module Tests")
        print("-" * 70)
        self.test_sentry_import()
        self.test_backup_help()

        print("\n🌐 API Endpoint Tests (requires running server)")
        print("-" * 70)
        if self._check_server_running():
            self.test_health_endpoint("/health/")
            self.test_health_endpoint("/health/live")
            self.test_health_endpoint("/health/ready")
            self.test_health_endpoint("/health/startup")
            self.test_detailed_health()
        else:
            logger.warning(f"⚠ Server not running at {self.base_url}")
            logger.info("  Skipping endpoint tests")
            logger.info("  Start server with: python -m uvicorn app.main:app")

        print("\n" + "=" * 70)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 70)

        return self.failed == 0

    def _check_server_running(self):
        """Check if server is running"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", self.base_url],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False


def main():
    """Run tests"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Vendly POS Monitoring Integration Tests"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for API tests",
    )
    parser.add_argument(
        "--db-url",
        help="Database URL for backup tests",
    )

    args = parser.parse_args()

    tests = MonitoringTests(base_url=args.base_url, db_url=args.db_url or "")
    success = tests.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
