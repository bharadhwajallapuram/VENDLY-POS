"""
Vendly POS - Backup Scheduler
==============================
APScheduler integration for automated backup jobs
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.models import BackupJob, BackupLog
from app.db.session import SessionLocal
from app.services.backup import BackupStatus, get_backup_service

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Manages scheduled backup jobs using APScheduler"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._loaded_jobs = set()

    def start(self):
        """Start the backup scheduler"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.is_running = True
                logger.info("[OK] Backup scheduler started")

                # Load existing jobs from database
                self._load_jobs_from_db()
        except Exception as e:
            logger.error(f"[ERROR] Failed to start backup scheduler: {e}")
            self.is_running = False

    def stop(self):
        """Stop the backup scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("[OK] Backup scheduler stopped")
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop backup scheduler: {e}")

    def _load_jobs_from_db(self):
        """Load and schedule all enabled backup jobs from database"""
        try:
            db = SessionLocal()
            try:
                jobs = db.query(BackupJob).filter(BackupJob.is_enabled == True).all()

                for job in jobs:
                    self._schedule_job(job)
                    self._loaded_jobs.add(job.id)

                logger.info(f"[OK] Loaded {len(jobs)} backup jobs from database")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[ERROR] Failed to load backup jobs from database: {e}")

    def _schedule_job(self, backup_job: BackupJob):
        """Schedule a single backup job"""
        try:
            job_id = f"backup_job_{backup_job.id}"

            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            # Create trigger based on schedule type
            trigger = self._create_trigger(backup_job)

            if trigger:
                self.scheduler.add_job(
                    self._execute_backup,
                    trigger=trigger,
                    id=job_id,
                    name=backup_job.name,
                    args=[backup_job.id, backup_job.backup_type],
                    misfire_grace_time=60,
                    coalesce=True,
                    replace_existing=True,
                )

                logger.info(
                    f"[OK] Scheduled backup job: {backup_job.name} (ID: {backup_job.id})"
                )
        except Exception as e:
            logger.error(
                f"[ERROR] Failed to schedule backup job {backup_job.name}: {e}"
            )

    def _create_trigger(self, backup_job: BackupJob) -> Optional[CronTrigger]:
        """Create APScheduler trigger based on schedule type"""
        try:
            if backup_job.schedule_type == "hourly":
                return CronTrigger(minute=0)  # Every hour

            elif backup_job.schedule_type == "daily":
                # Parse schedule_time (format: HH:MM)
                if backup_job.schedule_time:
                    hour, minute = map(int, backup_job.schedule_time.split(":"))
                    return CronTrigger(hour=hour, minute=minute)
                else:
                    return CronTrigger(hour=2, minute=0)  # Default: 2 AM

            elif backup_job.schedule_type == "weekly":
                # Default: Sunday at 2 AM
                if backup_job.schedule_time:
                    hour, minute = map(int, backup_job.schedule_time.split(":"))
                    return CronTrigger(day_of_week=6, hour=hour, minute=minute)
                else:
                    return CronTrigger(day_of_week=6, hour=2, minute=0)

            elif backup_job.schedule_type == "monthly":
                # Default: First day of month at 2 AM
                if backup_job.schedule_time:
                    hour, minute = map(int, backup_job.schedule_time.split(":"))
                    return CronTrigger(day=1, hour=hour, minute=minute)
                else:
                    return CronTrigger(day=1, hour=2, minute=0)

            else:
                logger.warning(f"Unknown schedule type: {backup_job.schedule_type}")
                return None
        except Exception as e:
            logger.error(f"[ERROR] Failed to create trigger: {e}")
            return None

    def _execute_backup(self, job_id: int, backup_type: str):
        """Execute a backup job (called by scheduler)"""
        try:
            db = SessionLocal()
            try:
                # Get job
                backup_job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
                if not backup_job:
                    logger.warning(f"Backup job {job_id} not found in database")
                    return

                # Update job status
                backup_job.last_run_at = datetime.utcnow()
                backup_job.last_run_status = BackupStatus.in_progress.value
                db.commit()

                # Execute backup
                logger.info(f"Executing backup job: {backup_job.name}")
                backup_service = get_backup_service()

                # Run async backup
                result = asyncio.run(
                    self._run_backup_async(backup_service, backup_type, backup_job)
                )

                # Update job with result
                backup_job.last_run_status = result.get("status")

                if result.get("status") == BackupStatus.completed.value:
                    # Create backup log
                    backup_log = BackupLog(
                        job_id=backup_job.id,
                        backup_id=result.get("backup_id", ""),
                        backup_type=backup_type,
                        status=BackupStatus.completed.value,
                        file_key=result.get("file_key"),
                        record_count=result.get("records", 0),
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                    )
                    db.add(backup_log)

                    # Clean up old backups
                    asyncio.run(
                        backup_service.delete_old_backups(backup_job.retention_days)
                    )

                else:
                    # Log failure
                    backup_log = BackupLog(
                        job_id=backup_job.id,
                        backup_id=result.get("backup_id", "unknown"),
                        backup_type=backup_type,
                        status=BackupStatus.failed.value,
                        error_message=result.get("error", "Unknown error"),
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                    )
                    db.add(backup_log)

                db.commit()
                logger.info(
                    f"[OK] Backup job completed: {backup_job.name} - Status: {result.get('status')}"
                )

            finally:
                db.close()
        except Exception as e:
            logger.error(f"[ERROR] Error executing backup job {job_id}: {e}")

    async def _run_backup_async(self, backup_service, backup_type: str, backup_job):
        """Run backup operation based on type"""
        try:
            if backup_type == "sales":
                return await backup_service.backup_sales_data()
            elif backup_type == "inventory":
                return await backup_service.backup_inventory_data()
            elif backup_type == "full":
                return await backup_service.backup_all_data()
            else:
                return {
                    "status": BackupStatus.failed.value,
                    "error": f"Unknown backup type: {backup_type}",
                }
        except Exception as e:
            return {
                "status": BackupStatus.failed.value,
                "error": str(e),
            }

    def add_or_update_job(self, backup_job: BackupJob):
        """Add or update a backup job in the scheduler"""
        try:
            if backup_job.is_enabled:
                self._schedule_job(backup_job)
                self._loaded_jobs.add(backup_job.id)
            else:
                # Remove job if disabled
                job_id = f"backup_job_{backup_job.id}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                self._loaded_jobs.discard(backup_job.id)
        except Exception as e:
            logger.error(f"[ERROR] Failed to add/update backup job: {e}")

    def remove_job(self, job_id: int):
        """Remove a backup job from the scheduler"""
        try:
            scheduler_job_id = f"backup_job_{job_id}"
            if self.scheduler.get_job(scheduler_job_id):
                self.scheduler.remove_job(scheduler_job_id)
            self._loaded_jobs.discard(job_id)
            logger.info(f"[OK] Removed backup job: {job_id}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to remove backup job: {e}")

    def get_scheduled_jobs(self) -> list:
        """Get list of currently scheduled jobs"""
        return self.scheduler.get_jobs()


# Global scheduler instance
_scheduler: Optional[BackupScheduler] = None


def get_backup_scheduler() -> BackupScheduler:
    """Get or create backup scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackupScheduler()
    return _scheduler
