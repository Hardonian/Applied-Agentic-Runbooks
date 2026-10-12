#!/usr/bin/env bash
# Stage only the reviewable artifacts owned by the readiness workflows.
#
# Do not replace this with `git add -A`: an audit must never gain the ability
# to commit arbitrary repository files merely because it ran in CI.
set -euo pipefail

readonly artifacts=(
  "security-reports/security_audit_summary_current.md"
  "docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md"
  "docs/DATAROOM_FILL_GUIDE.md"
  "yc/METRICS_SNAPSHOT.md"
  "yc/UNIT_ECONOMICS.md"
  "docs/WEEKLY_PROGRESS.md"
  "readiness-report.txt"
)

for artifact in "${artifacts[@]}"; do
  if [[ -e "$artifact" ]]; then
    git add -A -- "$artifact"
  fi
done
