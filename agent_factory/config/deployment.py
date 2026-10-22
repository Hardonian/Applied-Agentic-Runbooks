"""
Deployment configuration and profiles.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeploymentType(str, Enum):
    """Deployment type."""

    LOCAL_DEV = "local_dev"
    DOCKER_MONOLITH = "docker_monolith"
    SERVERLESS_API = "serverless_api"
    EDGE_RUNNER = "edge_runner"
    KUBERNETES = "kubernetes"


@dataclass
class DeploymentConfig:
    """
    Deployment configuration.

    Defines how Agent Factory is deployed and what external services it uses.
    """

    deployment_type: DeploymentType = DeploymentType.LOCAL_DEV

    # Database
    database_url: str | None = None
    database_type: str = "sqlite"  # sqlite, postgres

    # Cache/Queue
    redis_url: str | None = None
    use_redis: bool = False

    # Storage
    telemetry_backend: str = "sqlite"  # sqlite, postgres, s3
    prompt_log_backend: str = "sqlite"  # sqlite, postgres, s3

    # Job Queue
    job_queue_backend: str = "sqlite"  # sqlite, redis, sqs
    job_queue_url: str | None = None

    # Object Storage (for blueprints, artifacts)
    object_storage_type: str = "local"  # local, s3, gcs
    object_storage_url: str | None = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Workers
    worker_enabled: bool = True
    worker_count: int = 1

    # Features
    enable_telemetry: bool = True
    enable_billing: bool = True
    enable_auth: bool = True

    # Environment
    environment: str = "development"
    debug: bool = False

    # Additional config
    extra_config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "DeploymentConfig":
        """
        Create deployment config from environment variables.

        Returns:
            Deployment config
        """
        deployment_type_str = os.getenv("DEPLOYMENT_TYPE", "local_dev")
        try:
            deployment_type = DeploymentType(deployment_type_str)
        except ValueError:
            deployment_type = DeploymentType.LOCAL_DEV

        config = cls(
            deployment_type=deployment_type,
            database_url=os.getenv("DATABASE_URL"),
            database_type=os.getenv("DATABASE_TYPE", "sqlite"),
            redis_url=os.getenv("REDIS_URL"),
            use_redis=bool(os.getenv("REDIS_URL")),
            telemetry_backend=os.getenv("TELEMETRY_BACKEND", "sqlite"),
            prompt_log_backend=os.getenv("PROMPT_LOG_BACKEND", "sqlite"),
            job_queue_backend=os.getenv("JOB_QUEUE_BACKEND", "sqlite"),
            job_queue_url=os.getenv("JOB_QUEUE_URL"),
            object_storage_type=os.getenv("OBJECT_STORAGE_TYPE", "local"),
            object_storage_url=os.getenv("OBJECT_STORAGE_URL"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            api_workers=int(os.getenv("API_WORKERS", "1")),
            worker_enabled=os.getenv("WORKER_ENABLED", "true").lower() == "true",
            worker_count=int(os.getenv("WORKER_COUNT", "1")),
            enable_telemetry=os.getenv("ENABLE_TELEMETRY", "true").lower() == "true",
            enable_billing=os.getenv("ENABLE_BILLING", "true").lower() == "true",
            enable_auth=os.getenv("ENABLE_AUTH", "true").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

        return config

    def get_database_url(self) -> str:
        """
        Get database URL based on config.

        Returns:
            Database URL
        """
        if self.database_url:
            return self.database_url

        if self.database_type == "postgres":
            return os.getenv("DATABASE_URL", "postgresql://localhost/agent_factory")
        else:
            # SQLite
            return "./agent_factory/data.db"

    def get_telemetry_backend_class(self):
        """
        Get telemetry backend class based on config.

        Returns:
            Telemetry backend class
        """
        if self.telemetry_backend == "postgres":
            from agent_factory.telemetry.backends.postgres import PostgresTelemetryBackend

            return PostgresTelemetryBackend
        else:
            from agent_factory.telemetry.backends.sqlite import SQLiteTelemetryBackend

            return SQLiteTelemetryBackend

    def get_job_queue_class(self):
        """
        Get job queue class based on config.

        Returns:
            Job queue class
        """
        if self.job_queue_backend == "redis":
            # TODO: Implement RedisJobQueue
            from agent_factory.runtime.jobs import SQLiteJobQueue

            return SQLiteJobQueue
        else:
            from agent_factory.runtime.jobs import SQLiteJobQueue

            return SQLiteJobQueue


# Global deployment config
_deployment_config: DeploymentConfig | None = None


def get_deployment_config() -> DeploymentConfig:
    """
    Get global deployment config.

    Returns:
        Deployment config
    """
    global _deployment_config
    if _deployment_config is None:
        _deployment_config = DeploymentConfig.from_env()
    return _deployment_config
