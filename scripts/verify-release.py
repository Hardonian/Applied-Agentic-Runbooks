#!/usr/bin/env python3
"""Verify release metadata is internally consistent before publishing."""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def version_in(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ValueError(f"No version found in {path.relative_to(ROOT)}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Expected git tag, for example v0.2.0")
    args = parser.parse_args()

    pyproject_version = version_in(ROOT / "pyproject.toml", r'^version\s*=\s*"([^"]+)"')
    package_version = version_in(
        ROOT / "agent_factory" / "__init__.py", r'^__version__\s*=\s*"([^"]+)"'
    )

    errors = []
    if package_version != pyproject_version:
        errors.append(
            f"agent_factory.__version__ ({package_version}) does not match pyproject.toml ({pyproject_version})"
        )
    if args.tag and args.tag != f"v{pyproject_version}":
        errors.append(f"tag {args.tag} does not match version v{pyproject_version}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(
        rf"^## \[{re.escape(pyproject_version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        changelog,
        re.MULTILINE,
    ):
        errors.append(f"CHANGELOG.md has no dated entry for {pyproject_version}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Release metadata verified for v{pyproject_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
