"""
Tests for Cloud Backup Service
================================
Unit tests for backup functionality
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.db.models import BackupJob, BackupLog
from app.services.backup import BackupProvider, BackupStatus, CloudBackupService
from app.services.backup_scheduler import BackupScheduler


@pytest.fixture
def backup_service():
    """Create a backup service instance with local provider"""
    with patch("app.services.backup.settings") as mock_settings:
        mock_settings.BACKUP_PROVIDER = "local"
        mock_settings.BACKUP_BUCKET = "test-bucket"
        mock_settings.BACKUP_LOCAL_PATH = "/tmp/test_backups"
        service = CloudBackupService()
    return service


@pytest.fixture
def backup_scheduler():
    """Create a backup scheduler instance"""
    return BackupScheduler()


class TestCloudBackupService:
    """Tests for CloudBackupService"""

    @pytest.mark.asyncio
    async def test_backup_sales_data(self, backup_service):
        """Test sales data backup"""
        with patch("app.services.backup.SessionLocal") as mock_session:
            # Mock database response
            mock_db = Mock()
            mock_result = Mock()
            mock_result.keys.return_value = ["id", "total", "created_at"]
            mock_result.fetchall.return_value = [
                (1, 100.0, datetime.now()),
                (2, 200.0, datetime.now()),
            ]
            mock_db.execute.return_value = mock_result
            mock_session.return_value = mock_db

            result = await backup_service.backup_sales_data()

            assert result["status"] == BackupStatus.completed.value
            assert result["type"] == "sales"
            assert "backup_id" in result

    @pytest.mark.asyncio
    async def test_backup_inventory_data(self, backup_service):
        """Test inventory data backup"""
        with patch("app.services.backup.SessionLocal") as mock_session:
            # Mock database response
            mock_db = Mock()
            mock_result = Mock()
            mock_result.keys.return_value = ["id", "name", "quantity"]
            mock_result.fetchall.return_value = [
                (1, "Product A", 100),
                (2, "Product B", 50),
            ]
            mock_db.execute.return_value = mock_result
            mock_session.return_value = mock_db

            result = await backup_service.backup_inventory_data()

            assert result["status"] == BackupStatus.completed.value
            assert result["type"] == "inventory"
            assert "backup_id" in result

    @pytest.mark.asyncio
    async def test_backup_all_data(self, backup_service):
        """Test complete data backup"""
        with patch.object(
            backup_service, "backup_sales_data", new_callable=AsyncMock
        ) as mock_sales, patch.object(
            backup_service, "backup_inventory_data", new_callable=AsyncMock
        ) as mock_inventory:

            mock_sales.return_value = {
                "backup_id": "sales_123",
                "type": "sales",
                "status": BackupStatus.completed.value,
                "records": 100,
            }
            mock_inventory.return_value = {
                "backup_id": "inventory_123",
                "type": "inventory",
                "status": BackupStatus.completed.value,
                "records": 50,
            }

            result = await backup_service.backup_all_data()

            assert result["status"] == BackupStatus.completed.value
            assert result["successful_backups"] == 2
            mock_sales.assert_called_once()
            mock_inventory.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_backups(self, backup_service):
        """Test listing backups"""
        backups = await backup_service.list_backups()
        assert isinstance(backups, list)

    @pytest.mark.asyncio
    async def test_delete_old_backups(self, backup_service):
        """Test cleanup of old backups"""
        result = await backup_service.delete_old_backups(retention_days=30)

        assert "status" in result
        assert "deleted_count" in result

    def test_generate_backup_id(self, backup_service):
        """Test backup ID generation"""
        backup_id_1 = CloudBackupService._generate_backup_id("sales")
        backup_id_2 = CloudBackupService._generate_backup_id("sales")

        assert backup_id_1.startswith("sales_")
        assert backup_id_2.startswith("sales_")
        assert backup_id_1 != backup_id_2  # Should be unique

    def test_backup_provider_initialization(self):
        """Test backup provider initialization"""
        with patch("app.services.backup.settings") as mock_settings:
            mock_settings.BACKUP_PROVIDER = "local"
            mock_settings.BACKUP_BUCKET = "test"
            mock_settings.BACKUP_LOCAL_PATH = "/tmp"

            service = CloudBackupService()
            assert service.is_initialized is True
            assert service.provider == BackupProvider.local


class TestBackupScheduler:
    """Tests for BackupScheduler"""

    def test_scheduler_initialization(self, backup_scheduler):
        """Test scheduler initialization"""
        assert backup_scheduler.scheduler is not None
        assert backup_scheduler.is_running is False

    def test_scheduler_start_stop(self, backup_scheduler):
        """Test scheduler start and stop"""
        backup_scheduler.start()
        assert backup_scheduler.is_running is True

        backup_scheduler.stop()
        assert backup_scheduler.is_running is False

    def test_create_hourly_trigger(self, backup_scheduler):
        """Test hourly trigger creation"""
        mock_job = Mock()
        mock_job.schedule_type = "hourly"
        mock_job.schedule_time = None

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is not None

    def test_create_daily_trigger(self, backup_scheduler):
        """Test daily trigger creation"""
        mock_job = Mock()
        mock_job.schedule_type = "daily"
        mock_job.schedule_time = "02:00"

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is not None

    def test_create_weekly_trigger(self, backup_scheduler):
        """Test weekly trigger creation"""
        mock_job = Mock()
        mock_job.schedule_type = "weekly"
        mock_job.schedule_time = "02:00"

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is not None

    def test_create_monthly_trigger(self, backup_scheduler):
        """Test monthly trigger creation"""
        mock_job = Mock()
        mock_job.schedule_type = "monthly"
        mock_job.schedule_time = "02:00"

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is not None

    def test_create_invalid_trigger(self, backup_scheduler):
        """Test invalid schedule type"""
        mock_job = Mock()
        mock_job.schedule_type = "invalid"

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is None


class TestBackupModels:
    """Tests for backup database models"""

    def test_backup_job_creation(self):
        """Test BackupJob model creation"""
        job = BackupJob(
            name="Test Backup",
            backup_type="sales",
            schedule_type="daily",
            schedule_time="02:00",
            retention_days=30,
            is_enabled=True,
        )

        assert job.name == "Test Backup"
        assert job.backup_type == "sales"
        assert job.is_enabled is True

    def test_backup_log_creation(self):
        """Test BackupLog model creation"""
        log = BackupLog(
            backup_id="sales_123",
            backup_type="sales",
            status=BackupStatus.completed.value,
            file_key="backups/sales/sales_123.json.gz",
            record_count=100,
        )

        assert log.backup_id == "sales_123"
        assert log.status == BackupStatus.completed.value
        assert log.record_count == 100


class TestBackupIntegration:
    """Integration tests for backup system"""

    @pytest.mark.asyncio
    async def test_full_backup_workflow(self, backup_service):
        """Test complete backup workflow"""
        # Create backup
        with patch("app.services.backup.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_result = Mock()
            mock_result.keys.return_value = ["id", "total"]
            mock_result.fetchall.return_value = [(1, 100.0)]
            mock_db.execute.return_value = mock_result
            mock_session.return_value = mock_db

            # Backup
            backup_result = await backup_service.backup_sales_data()
            assert backup_result["status"] == BackupStatus.completed.value

            # List backups
            backups = await backup_service.list_backups("sales")
            assert isinstance(backups, list)

    def test_scheduler_job_management(self, backup_scheduler):
        """Test scheduler job add/remove operations"""
        mock_job = Mock(spec=BackupJob)
        mock_job.id = 1
        mock_job.name = "Test Job"
        mock_job.schedule_type = "daily"
        mock_job.schedule_time = "02:00"
        mock_job.is_enabled = True

        # Add job
        backup_scheduler.add_or_update_job(mock_job)
        assert 1 in backup_scheduler._loaded_jobs

        # Remove job
        backup_scheduler.remove_job(1)
        assert 1 not in backup_scheduler._loaded_jobs


class TestErrorHandling:
    """Tests for error handling in backup system"""

    @pytest.mark.asyncio
    async def test_backup_failure_handling(self, backup_service):
        """Test graceful handling of backup failures"""
        with patch("app.services.backup.SessionLocal") as mock_session:
            mock_session.side_effect = Exception("Database error")

            result = await backup_service.backup_sales_data()

            assert result["status"] == BackupStatus.failed.value
            assert "error" in result

    def test_invalid_schedule_handling(self, backup_scheduler):
        """Test handling of invalid schedule configuration"""
        mock_job = Mock(spec=BackupJob)
        mock_job.schedule_type = "invalid"

        trigger = backup_scheduler._create_trigger(mock_job)
        assert trigger is None

    @pytest.mark.asyncio
    async def test_cloud_provider_connection_error(self):
        """Test handling of cloud provider connection errors"""
        with patch("app.services.backup.settings") as mock_settings:
            mock_settings.BACKUP_PROVIDER = "s3"
            mock_settings.BACKUP_BUCKET = "test"

            with patch("boto3.client") as mock_boto:
                mock_boto.side_effect = Exception("Connection failed")

                service = CloudBackupService()
                assert service.is_initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
