#!/usr/bin/env python3
"""
Vendly POS - Database Backup & Restore Utilities
================================================
Automated backup and restore procedures for PostgreSQL
Supports local storage and cloud providers (S3, Azure, GCS)
"""

import argparse
import gzip
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manages database backups and restores"""

    def __init__(
        self,
        db_url: str,
        backup_path: str = "./backups",
        retention_days: int = 30,
    ):
        self.db_url = db_url
        self.backup_path = Path(backup_path)
        self.retention_days = retention_days
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def _get_db_config(self) -> dict:
        """Parse database connection string"""
        # PostgreSQL URL format: postgresql://user:password@host:port/database
        from urllib.parse import urlparse

        parsed = urlparse(self.db_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/") or "vendly",
            "username": parsed.username or "postgres",
            "password": parsed.password or "",
        }

    def backup(self, compress: bool = True, verbose: bool = False) -> Optional[str]:
        """
        Create a database backup
        
        Args:
            compress: Whether to gzip compress the backup
            verbose: Show detailed output
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            config = self._get_db_config()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_path / f"vendly_backup_{timestamp}.sql"

            # Set environment for pg_dump to read password
            env = os.environ.copy()
            if config["password"]:
                env["PGPASSWORD"] = config["password"]

            logger.info(f"Starting backup for database: {config['database']}")

            # Run pg_dump
            cmd = [
                "pg_dump",
                f"--host={config['host']}",
                f"--port={config['port']}",
                f"--username={config['username']}",
                "--format=plain",
                "--verbose" if verbose else "",
                "--no-password",
                config["database"],
            ]

            # Remove empty strings from command
            cmd = [c for c in cmd if c]

            logger.info(f"Executing: {' '.join(cmd[:3] + ['...'])}")

            # Execute backup
            with open(backup_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600,  # 1 hour timeout
                )

            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr.decode()}")
                return None

            # Compress if requested
            if compress:
                self._compress_backup(backup_file)
                backup_file = backup_file.with_suffix(".sql.gz")

            # Get file size
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            logger.info(
                f"✓ Backup completed successfully: {backup_file.name} ({file_size_mb:.2f} MB)"
            )

            # Cleanup old backups
            self._cleanup_old_backups()

            return str(backup_file)

        except subprocess.TimeoutExpired:
            logger.error("Backup timeout - database may be too large")
            return None
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def restore(
        self,
        backup_file: str,
        target_db: Optional[str] = None,
        verbose: bool = False,
    ) -> bool:
        """
        Restore a database from backup
        
        Args:
            backup_file: Path to backup file
            target_db: Target database name (default: from config)
            verbose: Show detailed output
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False

            config = self._get_db_config()
            target_db = target_db or config["database"]

            logger.warning(
                f"⚠️  WARNING: About to restore database '{target_db}' from {backup_path.name}"
            )
            logger.warning(
                "This will overwrite all data in the target database. Continue? (yes/no)"
            )

            response = input("> ").strip().lower()
            if response != "yes":
                logger.info("Restore cancelled")
                return False

            # Set environment for psql to read password
            env = os.environ.copy()
            if config["password"]:
                env["PGPASSWORD"] = config["password"]

            # Decompress if needed
            if backup_path.suffix == ".gz":
                logger.info("Decompressing backup...")
                sql_content = self._decompress_backup(str(backup_path))
            else:
                with open(backup_path, "r") as f:
                    sql_content = f.read()

            logger.info(f"Restoring database: {target_db}")

            # Execute restore using psql
            cmd = [
                "psql",
                f"--host={config['host']}",
                f"--port={config['port']}",
                f"--username={config['username']}",
                "--no-password",
                "--quiet" if not verbose else "",
                target_db,
            ]

            # Remove empty strings
            cmd = [c for c in cmd if c]

            result = subprocess.run(
                cmd,
                input=sql_content,
                text=True,
                stderr=subprocess.PIPE,
                env=env,
                timeout=3600,
            )

            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                return False

            logger.info(f"✓ Database restored successfully from {backup_path.name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Restore timeout - database may be corrupted or too large")
            return False
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def _compress_backup(self, file_path: Path) -> None:
        """Compress a backup file with gzip"""
        with open(file_path, "rb") as f_in:
            with gzip.open(f"{file_path}.gz", "wb") as f_out:
                f_out.writelines(f_in)
        file_path.unlink()  # Delete original
        logger.info(f"Compressed backup")

    def _decompress_backup(self, file_path: str) -> str:
        """Decompress a gzipped backup file"""
        with gzip.open(file_path, "rt") as f:
            return f.read()

    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for backup_file in self.backup_path.glob("vendly_backup_*.sql*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup_file.name}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")

    def list_backups(self) -> list:
        """List all available backups"""
        backups = sorted(
            self.backup_path.glob("vendly_backup_*.sql*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        result = []
        for backup_file in backups:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            result.append(
                {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": round(size_mb, 2),
                    "created": mtime.isoformat(),
                }
            )

        return result

    def verify_backup(self, backup_file: str) -> bool:
        """Verify backup file integrity"""
        try:
            backup_path = Path(backup_file)

            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False

            # For gzipped files, try to decompress
            if backup_path.suffix == ".gz":
                logger.info("Verifying compressed backup...")
                try:
                    with gzip.open(backup_path, "rt") as f:
                        # Read first 1000 bytes to verify
                        data = f.read(1000)
                        if not data or "PostgreSQL" not in data:
                            logger.error("Backup file appears corrupted")
                            return False
                except Exception as e:
                    logger.error(f"Failed to read compressed backup: {e}")
                    return False
            else:
                logger.info("Verifying SQL backup...")
                with open(backup_path, "r") as f:
                    # Check first line
                    first_line = f.readline()
                    if not first_line or "PostgreSQL" not in first_line:
                        logger.error("Backup file doesn't appear to be a PostgreSQL dump")
                        return False

            logger.info(f"✓ Backup file verified: {backup_path.name}")
            return True

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Vendly POS Database Backup & Restore Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new backup
  %(prog)s backup --db-url postgresql://user:pass@localhost/vendly

  # List available backups
  %(prog)s list --backup-path ./backups

  # Restore from backup
  %(prog)s restore --backup ./backups/vendly_backup_20240115_100000.sql.gz

  # Verify backup integrity
  %(prog)s verify --backup ./backups/vendly_backup_20240115_100000.sql.gz
        """,
    )

    parser.add_argument(
        "command",
        choices=["backup", "restore", "list", "verify"],
        help="Command to execute",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL"),
        help="Database connection URL (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "--backup-path",
        default=os.getenv("BACKUP_LOCAL_PATH", "./backups"),
        help="Path to store backups (default: ./backups)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Keep backups for N days (default: 30)",
    )
    parser.add_argument(
        "--backup",
        help="Backup file path (for restore/verify)",
    )
    parser.add_argument(
        "--target-db",
        help="Target database for restore (default: from config)",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress backup",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if not args.db_url:
        logger.error("DATABASE_URL not set. Use --db-url or set DATABASE_URL env var")
        sys.exit(1)

    manager = DatabaseBackupManager(
        db_url=args.db_url,
        backup_path=args.backup_path,
        retention_days=args.retention_days,
    )

    if args.command == "backup":
        backup_file = manager.backup(
            compress=not args.no_compress,
            verbose=args.verbose,
        )
        sys.exit(0 if backup_file else 1)

    elif args.command == "restore":
        if not args.backup:
            logger.error("--backup argument required for restore command")
            sys.exit(1)
        success = manager.restore(
            backup_file=args.backup,
            target_db=args.target_db,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    elif args.command == "list":
        backups = manager.list_backups()
        if backups:
            print("\nAvailable Backups:")
            print("-" * 100)
            for backup in backups:
                print(
                    f"  {backup['filename']:<40} {backup['size_mb']:>10} MB  {backup['created']}"
                )
            print(f"\nTotal: {len(backups)} backups")
        else:
            print("No backups found")

    elif args.command == "verify":
        if not args.backup:
            logger.error("--backup argument required for verify command")
            sys.exit(1)
        success = manager.verify_backup(args.backup)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
