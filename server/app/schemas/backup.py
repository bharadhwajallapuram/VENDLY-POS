"""
Vendly POS - Backup Schemas
============================
Pydantic models for backup API request/response validation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BackupJobCreate(BaseModel):
    """Create a new backup job"""

    name: str = Field(..., min_length=1, max_length=255)
    backup_type: str = Field(
        ..., description="Type of backup: sales, inventory, or full"
    )
    schedule_type: str = Field(
        ..., description="Schedule frequency: hourly, daily, weekly, monthly"
    )
    schedule_time: Optional[str] = Field(None, description="Time to run (HH:MM format)")
    retention_days: int = Field(default=30, ge=1, le=365)
    is_enabled: bool = Field(default=True)


class BackupJobUpdate(BaseModel):
    """Update a backup job"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    backup_type: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_time: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    is_enabled: Optional[bool] = None


class BackupJobResponse(BaseModel):
    """Backup job response"""

    id: int
    name: str
    backup_type: str
    schedule_type: str
    schedule_time: Optional[str]
    retention_days: int
    is_enabled: bool
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BackupLogResponse(BaseModel):
    """Backup log entry response"""

    id: int
    job_id: Optional[int]
    backup_id: str
    backup_type: str
    status: str
    file_key: Optional[str]
    file_size: Optional[int]
    record_count: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BackupResponse(BaseModel):
    """Backup operation response"""

    backup_id: Optional[str] = None
    type: Optional[str] = None
    status: str
    records: Optional[int] = None
    file_key: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime
    successful_backups: Optional[int] = None
    failed_backups: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class BackupListResponse(BaseModel):
    """List of backups response"""

    backups: List[Dict[str, Any]]
    count: int
    backup_type: Optional[str] = None


class BackupStatusResponse(BaseModel):
    """Backup system status response"""

    service_initialized: bool
    provider: str
    total_backups: int
    successful_backups: int
    failed_backups: int
    last_backup_time: Optional[str]
    enabled_jobs: int
