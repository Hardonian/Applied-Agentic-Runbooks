"""Deployment configuration contracts."""

import pytest

from agent_factory.config.deployment import DeploymentConfig
from agent_factory.jobs.queue import RedisJobQueue
from agent_factory.runtime.jobs import SQLiteJobQueue


def test_selects_redis_queue_when_configured() -> None:
    assert DeploymentConfig(job_queue_backend="redis").get_job_queue_class() is RedisJobQueue


def test_selects_sqlite_queue_when_configured() -> None:
    assert DeploymentConfig(job_queue_backend="sqlite").get_job_queue_class() is SQLiteJobQueue


def test_rejects_unimplemented_queue_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported job queue backend"):
        DeploymentConfig(job_queue_backend="sqs").get_job_queue_class()
