"""Fail CI when repository-wide Ruff or mypy debt exceeds the checked-in baseline."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".quality-baseline.json"


def count(command: list[str], pattern: str) -> int:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(pattern, output)
    return int(match.group(1)) if match else 0


def main() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    current = {
        "ruff": count(["ruff", "check", "agent_factory", "tests"], r"Found (\d+) errors?"),
        "mypy": count(["mypy", "agent_factory", "--no-error-summary"], r"(?m)^(?:.* error:.*\n?)+"),
    }
    # Mypy emits one line per error; the regex aggregate is not count-friendly.
    mypy = subprocess.run(
        ["mypy", "agent_factory", "--no-error-summary"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    current["mypy"] = sum(" error:" in line for line in mypy.stdout.splitlines())
    print(json.dumps({"baseline": baseline, "current": current}, indent=2))
    regressions = [name for name, value in current.items() if value > int(baseline[name])]
    if regressions:
        print(f"Quality debt increased: {', '.join(regressions)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
