"""
Vendly POS - Backup API Endpoints
===================================
REST API for managing cloud backups of sales and inventory data
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import BackupJob, BackupLog, User
from app.schemas.backup import (
    BackupJobCreate,
    BackupJobResponse,
    BackupJobUpdate,
    BackupListResponse,
    BackupLogResponse,
    BackupResponse,
)
from app.services.backup import BackupStatus, get_backup_service

router = APIRouter(prefix="/api/v1/backups", tags=["Backups"])


# ==================== BACKUP OPERATIONS ====================


@router.post("/sales", response_model=BackupResponse)
async def backup_sales_data(
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Trigger a manual backup of sales data

    - **Admin only**: Requires admin role
    - **Date Range**: Optional start_date and end_date parameters
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    result = await backup_service.backup_sales_data(start_date, end_date)

    # Log backup in database
    if result.get("status") == BackupStatus.completed.value:
        backup_log = BackupLog(
            backup_id=result.get("backup_id"),
            backup_type="sales",
            status=result.get("status"),
            file_key=result.get("file_key"),
            record_count=result.get("records", 0),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(backup_log)
        db.commit()

    return result


@router.post("/inventory", response_model=BackupResponse)
async def backup_inventory_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger a manual backup of inventory (products) data

    - **Admin only**: Requires admin role
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    result = await backup_service.backup_inventory_data()

    # Log backup in database
    if result.get("status") == BackupStatus.completed.value:
        backup_log = BackupLog(
            backup_id=result.get("backup_id"),
            backup_type="inventory",
            status=result.get("status"),
            file_key=result.get("file_key"),
            record_count=result.get("records", 0),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(backup_log)
        db.commit()

    return result


@router.post("/full", response_model=BackupResponse)
async def backup_all_data(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Trigger a complete backup of all data (sales, inventory, etc.)

    - **Admin only**: Requires admin role
    - **Background**: Full backups run in the background
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    # Run backup asynchronously
    if background_tasks:
        background_tasks.add_task(backup_service.backup_all_data)

    result = await backup_service.backup_all_data()

    return result


@router.get("/list", response_model=BackupListResponse)
async def list_backups(
    current_user: User = Depends(get_current_user),
    backup_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List all available backups

    - **Admin only**: Requires admin role
    - **Types**: Filter by 'sales', 'inventory', etc. (optional)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    backups = await backup_service.list_backups(backup_type)

    return {
        "backups": backups,
        "count": len(backups),
        "backup_type": backup_type,
    }


@router.post("/restore/{backup_id}", response_model=BackupResponse)
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Restore data from a specific backup

    - **Admin only**: Requires admin role
    - **Caution**: This will overwrite existing data
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    result = await backup_service.restore_sales_data(backup_id)

    return result


@router.delete("/cleanup", response_model=dict)
async def cleanup_old_backups(
    current_user: User = Depends(get_current_user),
    retention_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Delete backups older than retention period

    - **Admin only**: Requires admin role
    - **Retention**: Default 30 days, can specify 1-365 days
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    if not backup_service.is_initialized:
        raise HTTPException(status_code=503, detail="Backup service is not initialized")

    result = await backup_service.delete_old_backups(retention_days)

    return result


# ==================== BACKUP JOB MANAGEMENT ====================


@router.post("/jobs", response_model=BackupJobResponse)
async def create_backup_job(
    job_data: BackupJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a scheduled backup job

    - **Admin only**: Requires admin role
    - **Schedule Types**: hourly, daily, weekly, monthly
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if job with same name exists
    existing = db.query(BackupJob).filter(BackupJob.name == job_data.name).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Backup job with this name already exists"
        )

    job = BackupJob(
        name=job_data.name,
        backup_type=job_data.backup_type,
        schedule_type=job_data.schedule_type,
        schedule_time=job_data.schedule_time,
        retention_days=job_data.retention_days,
        is_enabled=job_data.is_enabled,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/jobs", response_model=List[BackupJobResponse])
async def list_backup_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all scheduled backup jobs

    - **Admin only**: Requires admin role
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    jobs = db.query(BackupJob).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=BackupJobResponse)
async def get_backup_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific backup job"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")

    return job


@router.put("/jobs/{job_id}", response_model=BackupJobResponse)
async def update_backup_job(
    job_id: int,
    job_data: BackupJobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a scheduled backup job"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")

    # Update fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return job


@router.delete("/jobs/{job_id}")
async def delete_backup_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a scheduled backup job"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")

    db.delete(job)
    db.commit()

    return {"status": "success", "message": "Backup job deleted"}


# ==================== BACKUP LOG VIEWING ====================


@router.get("/logs", response_model=List[BackupLogResponse])
async def list_backup_logs(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    backup_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List backup execution logs

    - **Admin only**: Requires admin role
    - **Pagination**: limit (1-500) and offset
    - **Filters**: Optional backup_type and status
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query = db.query(BackupLog)

    if backup_type:
        query = query.filter(BackupLog.backup_type == backup_type)

    if status:
        query = query.filter(BackupLog.status == status)

    logs = query.order_by(BackupLog.created_at.desc()).offset(offset).limit(limit).all()

    return logs


@router.get("/logs/{backup_id}", response_model=BackupLogResponse)
async def get_backup_log(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific backup log entry"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    log = db.query(BackupLog).filter(BackupLog.backup_id == backup_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Backup log not found")

    return log


@router.get("/status", response_model=dict)
async def get_backup_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get overall backup system status

    - **Admin only**: Requires admin role
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    backup_service = get_backup_service()

    # Get statistics
    total_backups = db.query(BackupLog).count()
    successful_backups = (
        db.query(BackupLog)
        .filter(BackupLog.status == BackupStatus.completed.value)
        .count()
    )
    failed_backups = (
        db.query(BackupLog)
        .filter(BackupLog.status == BackupStatus.failed.value)
        .count()
    )

    # Get last backup
    last_backup = db.query(BackupLog).order_by(BackupLog.created_at.desc()).first()

    # Get enabled jobs
    enabled_jobs = db.query(BackupJob).filter(BackupJob.is_enabled == True).count()

    return {
        "service_initialized": backup_service.is_initialized,
        "provider": backup_service.provider.value,
        "total_backups": total_backups,
        "successful_backups": successful_backups,
        "failed_backups": failed_backups,
        "last_backup_time": last_backup.created_at.isoformat() if last_backup else None,
        "enabled_jobs": enabled_jobs,
    }
