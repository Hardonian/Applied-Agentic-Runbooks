"""Unit tests for the external readiness heartbeat checker."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-readiness-heartbeat.py"
SPEC = importlib.util.spec_from_file_location("readiness_heartbeat", SCRIPT)
assert SPEC and SPEC.loader
heartbeat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(heartbeat)


def run(
    *, age_hours: float = 1, status: str = "completed", conclusion: str = "success"
) -> dict[str, str]:
    created = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return {"created_at": created.isoformat(), "status": status, "conclusion": conclusion}


def test_healthy_scheduled_run_passes() -> None:
    heartbeat.check_run(run(), max_age_hours=30)


@pytest.mark.parametrize(
    ("run_data", "expected"),
    [
        (run(age_hours=31), "old"),
        (run(status="in_progress"), "not completed"),
        (run(conclusion="failure"), "concluded"),
    ],
)
def test_unhealthy_scheduled_run_fails(run_data: dict[str, str], expected: str) -> None:
    with pytest.raises(RuntimeError, match=expected):
        heartbeat.check_run(run_data, max_age_hours=30)
