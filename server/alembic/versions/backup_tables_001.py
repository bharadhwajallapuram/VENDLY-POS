"""
Alembic migration for backup-related tables
Run with: alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa


revision = "backup_tables_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create backup_jobs and backup_logs tables"""

    # Create backup_jobs table
    op.create_table(
        "backup_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("backup_type", sa.String(50), nullable=False),
        sa.Column("schedule_type", sa.String(50), nullable=False),
        sa.Column("schedule_time", sa.String(50), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_status", sa.String(50), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create index on backup_jobs
    op.create_index("ix_backup_jobs_name", "backup_jobs", ["name"])

    # Create backup_logs table
    op.create_table(
        "backup_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("backup_id", sa.String(255), nullable=False, unique=True),
        sa.Column("backup_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["backup_jobs.id"]),
        sa.UniqueConstraint("backup_id"),
    )

    # Create indexes on backup_logs
    op.create_index("ix_backup_logs_job_id", "backup_logs", ["job_id"])
    op.create_index("ix_backup_logs_backup_id", "backup_logs", ["backup_id"])
    op.create_index("ix_backup_logs_created_at", "backup_logs", ["created_at"])
    op.create_index("ix_backup_logs_status", "backup_logs", ["status"])


def downgrade() -> None:
    """Drop backup-related tables"""

    op.drop_index("ix_backup_logs_status")
    op.drop_index("ix_backup_logs_created_at")
    op.drop_index("ix_backup_logs_backup_id")
    op.drop_index("ix_backup_logs_job_id")
    op.drop_table("backup_logs")

    op.drop_index("ix_backup_jobs_name")
    op.drop_table("backup_jobs")
