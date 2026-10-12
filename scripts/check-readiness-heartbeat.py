#!/usr/bin/env python3
"""Check that the scheduled readiness workflow is recent and successful.

The checker is deliberately usable outside GitHub Actions. Run it from an
external monitor to detect the failure mode where GitHub disables all schedule
triggers on an inactive repository.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import PurePosixPath
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY"), help="OWNER/REPO")
    parser.add_argument("--workflow", default="nightly-readiness.yml", help="workflow file or ID")
    parser.add_argument("--max-age-hours", type=float, default=30, help="maximum age of last scheduled run")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token; required for private repos")
    parser.add_argument("--api-url", default="https://api.github.com", help="GitHub API base URL")
    parser.add_argument("--json", action="store_true", help="emit the checked run as JSON")
    args = parser.parse_args()
    if not args.repo or "/" not in args.repo:
        parser.error("--repo OWNER/REPO is required (or set GITHUB_REPOSITORY)")
    if args.max_age_hours <= 0:
        parser.error("--max-age-hours must be positive")
    return args


def get_latest_run(args: argparse.Namespace) -> dict[str, Any]:
    owner, repo = args.repo.split("/", 1)
    workflow = quote(str(PurePosixPath(args.workflow)), safe="")
    url = (
        f"{args.api_url.rstrip('/')}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        f"/actions/workflows/{workflow}/runs?event=schedule&per_page=1"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-factory-readiness-heartbeat",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=15) as response:  # nosec B310: fixed GitHub API endpoint
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}; verify repository access and token scope") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc.reason}") from exc

    runs = payload.get("workflow_runs", [])
    if not runs:
        raise RuntimeError("No scheduled readiness run was found")
    return runs[0]


def check_run(run: dict[str, Any], max_age_hours: float) -> None:
    created_at = run.get("created_at")
    if not isinstance(created_at, str):
        raise RuntimeError("Latest scheduled run did not include created_at")
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"Invalid created_at from GitHub: {created_at!r}") from exc

    age = datetime.now(timezone.utc) - created.astimezone(timezone.utc)
    if age > timedelta(hours=max_age_hours):
        raise RuntimeError(f"Latest scheduled run is {age.total_seconds() / 3600:.1f}h old (limit {max_age_hours:g}h)")
    if run.get("status") != "completed":
        raise RuntimeError(f"Latest scheduled run is {run.get('status', 'unknown')!r}, not completed")
    if run.get("conclusion") != "success":
        raise RuntimeError(f"Latest scheduled run concluded {run.get('conclusion', 'unknown')!r}")


def main() -> int:
    args = parse_args()
    try:
        run = get_latest_run(args)
        check_run(run, args.max_age_hours)
    except RuntimeError as exc:
        print(f"Readiness heartbeat FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(run, indent=2, sort_keys=True))
    else:
        print(
            "Readiness heartbeat healthy: "
            f"run {run.get('id')} completed successfully at {run.get('updated_at', run.get('created_at'))}."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
