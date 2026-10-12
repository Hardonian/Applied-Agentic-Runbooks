#!/usr/bin/env python3
"""Verify the invariants documented by docs/RUNBOOK.md.

This intentionally checks repository configuration rather than contacting
GitHub, so it can run locally and in CI without credentials.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def require_text(path: Path, snippets: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path.relative_to(ROOT)}: missing {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    nightly = ROOT / ".github/workflows/nightly-readiness.yml"
    automated = ROOT / ".github/workflows/automated-readiness.yml"
    ci = ROOT / ".github/workflows/ci.yml"
    runbook = ROOT / "docs/RUNBOOK.md"
    makefile = ROOT / "Makefile"

    failures: list[str] = []
    for path in (nightly, automated, ci, runbook, makefile):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")

    if failures:
        print("Runbook contract failed:", *failures, sep="\n- ")
        return 1

    failures.extend(
        require_text(
            nightly,
            (
                "cron: '0 3 * * *'",
                "workflow_dispatch:",
                "contents: write",
                "pull-requests: write",
                "continue-on-error: true",
                "SKIP_INTERACTIVE=true",
                "git diff --staged --quiet",
                "pulls.list",
                "pulls.create",
            ),
        )
    )
    failures.extend(
        require_text(
            automated,
            (
                "contents: read",
                "This workflow intentionally does not write",
                "issues.createComment",
            ),
        )
    )
    failures.extend(require_text(ci, ("verify-runbook-contract.py",)))
    failures.extend(
        require_text(
            runbook,
            (
                "The Three Invariants",
                "Failure-Mode Matrix",
                "Verification Doctrine",
                "make verify-runbook",
            ),
        )
    )
    failures.extend(
        require_text(
            makefile,
            (
                "verify-runbook:",
                "dataroom-placeholders:",
                "user-acquisition:",
            ),
        )
    )

    if failures:
        print("Runbook contract failed:", *failures, sep="\n- ")
        return 1

    print("Runbook contract verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
