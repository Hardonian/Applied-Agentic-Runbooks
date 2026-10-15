"""
Database backup and restore system for Agent Factory Platform.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from agent_factory.core.exceptions import DatabaseError


class BackupManager:
    """
    Manages database backups and restores.
    
    Example:
        >>> manager = BackupManager()
        >>> backup_path = manager.create_backup()
        >>> manager.restore_backup(backup_path)
    """
    
    def __init__(self, backup_dir: str | None = None):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Backup directory (defaults to ./backups)
        """
        self.backup_dir = Path(backup_dir or "./backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./agent_factory.db")
    
    def create_backup(self, name: str | None = None) -> str:
        """
        Create a database backup.
        
        Args:
            name: Optional backup name
            
        Returns:
            Path to backup file
            
        Raises:
            DatabaseError: If backup fails
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        
        if self.database_url.startswith("sqlite"):
            # SQLite backup
            db_path = self.database_url.replace("sqlite:///", "")
            backup_path = self.backup_dir / f"{backup_name}.db"
            
            try:
                import shutil
                shutil.copy2(db_path, backup_path)
            except Exception as e:
                raise DatabaseError(f"SQLite backup failed: {e}") from e
        
        elif "postgresql" in self.database_url or "postgres" in self.database_url:
            # PostgreSQL backup using pg_dump
            backup_path = self.backup_dir / f"{backup_name}.sql"
            
            try:
                subprocess.run(
                    ["pg_dump", self.database_url],
                    stdout=open(backup_path, "w"),
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise DatabaseError(f"PostgreSQL backup failed: {e}") from e
            except FileNotFoundError:
                raise DatabaseError("pg_dump not found. Install PostgreSQL client tools.")
        
        else:
            raise DatabaseError(f"Unsupported database: {self.database_url}")
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str) -> None:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Raises:
            DatabaseError: If restore fails
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise DatabaseError(f"Backup file not found: {backup_path}")
        
        if self.database_url.startswith("sqlite"):
            # SQLite restore
            db_path = self.database_url.replace("sqlite:///", "")
            
            try:
                import shutil
                shutil.copy2(backup_file, db_path)
            except Exception as e:
                raise DatabaseError(f"SQLite restore failed: {e}") from e
        
        elif "postgresql" in self.database_url or "postgres" in self.database_url:
            # PostgreSQL restore using psql
            try:
                with open(backup_file, "r") as f:
                    subprocess.run(
                        ["psql", self.database_url],
                        stdin=f,
                        check=True,
                    )
            except subprocess.CalledProcessError as e:
                raise DatabaseError(f"PostgreSQL restore failed: {e}") from e
            except FileNotFoundError:
                raise DatabaseError("psql not found. Install PostgreSQL client tools.")
        
        else:
            raise DatabaseError(f"Unsupported database: {self.database_url}")
    
    def list_backups(self) -> list[dict]:
        """
        List available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        for backup_file in self.backup_dir.glob("*.sql"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Clean up old backups.
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Number of backups deleted
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=keep_days)
        deleted = 0
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff:
                    backup_file.unlink()
                    deleted += 1
        
        return deleted


def get_backup_manager() -> BackupManager:
    """Get backup manager instance."""
    return BackupManager()
