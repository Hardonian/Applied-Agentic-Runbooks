"""
Database migration system for Agent Factory Platform.

Provides versioned database schema migrations using Alembic.
"""

import os
from pathlib import Path

from alembic.runtime import migration

from agent_factory.core.exceptions import DatabaseError
from agent_factory.database.session import engine
from alembic import config as alembic_config
from alembic import script


class MigrationManager:
    """
    Manages database migrations.

    Example:
        >>> manager = MigrationManager()
        >>> manager.upgrade()
        >>> manager.current_revision()
    """

    def __init__(self, alembic_ini_path: str | None = None):
        """
        Initialize migration manager.

        Args:
            alembic_ini_path: Path to alembic.ini (defaults to project root)
        """
        self.alembic_ini_path = alembic_ini_path or self._find_alembic_ini()
        self.engine = engine

    def _find_alembic_ini(self) -> str:
        """Find alembic.ini file."""
        # Look for alembic.ini in project root
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        if not alembic_ini.exists():
            # Create default alembic.ini
            self._create_alembic_ini(alembic_ini)

        return str(alembic_ini)

    def _create_alembic_ini(self, path: Path) -> None:
        """Create default alembic.ini configuration."""
        alembic_dir = path.parent / "alembic"
        alembic_dir.mkdir(exist_ok=True)

        config_content = f"""[alembic]
script_location = {alembic_dir}
prepend_sys_path = .
sqlalchemy.url = {os.getenv('DATABASE_URL', 'sqlite:///./agent_factory.db')}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        path.write_text(config_content)

    def upgrade(self, revision: str = "head") -> None:
        """
        Upgrade database to specified revision.

        Args:
            revision: Target revision (default: "head")

        Raises:
            DatabaseError: If migration fails
        """
        try:
            from alembic import command

            cfg = alembic_config.Config(self.alembic_ini_path)
            command.upgrade(cfg, revision)
        except Exception as e:
            raise DatabaseError(f"Migration upgrade failed: {e}") from e

    def downgrade(self, revision: str) -> None:
        """
        Downgrade database to specified revision.

        Args:
            revision: Target revision

        Raises:
            DatabaseError: If migration fails
        """
        try:
            from alembic import command

            cfg = alembic_config.Config(self.alembic_ini_path)
            command.downgrade(cfg, revision)
        except Exception as e:
            raise DatabaseError(f"Migration downgrade failed: {e}") from e

    def current_revision(self) -> str | None:
        """
        Get current database revision.

        Returns:
            Current revision or None if no migrations applied
        """
        try:
            alembic_config.Config(self.alembic_ini_path)
            with self.engine.connect() as connection:
                context = migration.MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception:
            return None

    def create_revision(self, message: str, autogenerate: bool = True) -> str:
        """
        Create a new migration revision.

        Args:
            message: Migration message
            autogenerate: Auto-generate from models

        Returns:
            Revision identifier
        """
        try:
            from alembic import command

            cfg = alembic_config.Config(self.alembic_ini_path)
            command.revision(cfg, message=message, autogenerate=autogenerate)
            return self.current_revision() or "unknown"
        except Exception as e:
            raise DatabaseError(f"Failed to create revision: {e}") from e

    def history(self) -> list:
        """
        Get migration history.

        Returns:
            List of migration revisions
        """
        try:
            cfg = alembic_config.Config(self.alembic_ini_path)
            script_dir = script.ScriptDirectory.from_config(cfg)
            return [rev.revision for rev in script_dir.walk_revisions()]
        except Exception:
            return []


def init_migrations() -> MigrationManager:
    """
    Initialize migration system.

    Returns:
        MigrationManager instance
    """
    return MigrationManager()
