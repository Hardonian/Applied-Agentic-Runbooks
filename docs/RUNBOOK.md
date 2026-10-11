# The Self-Auditing Repo Runbook

**Turning a repository into a machine that reviews itself every night.**

Repo: `Hardonian/JupyterNotebooks` (Agent Factory) · Maintainer: Scott Hardie
Version: 2.0 (2026-10-11) · Status: production, runs unattended

---

> Most repos rot quietly. Docs drift, coverage drops, security findings pile up,
> and nobody notices until an investor, an audit, or an incident forces the
> question. This runbook documents the system we built so the repo answers that
> question **itself, every night at 03:00 UTC** — and opens its own PR with the
> receipts. It is a copy-paste playbook: every script, trigger, gotcha, and
> triage loop is documented. Adopt it on your repo in about an afternoon.

---

## 1. What This System Is

A closed loop of four parts:

```
┌─────────────────────────────────────────────────────────────┐
│  1. READINESS SCRIPTS   (bash/python in scripts/, Makefile) │
│  2. TRIGGERS            (GitHub Actions: nightly + on-PR)   │
│  3. GENERATED ARTIFACTS (reports committed back to the repo)│
│  4. TRIAGE LOOP         (nightly PR → review → merge)       │
└─────────────────────────────────────────────────────────────┘
```

- **Nightly (03:00 UTC):** runs every audit script, commits any generated
  changes to a dated branch, opens a PR: `🤖 Automated: Nightly Readiness
  Updates - YYYY-MM-DD`.
- **On every PR / push to main:** runs the same scripts, commits updates
  directly to the branch, and posts a summary comment on the PR.
- **You never babysit it.** Worst case, one PR comment per night tells you
  exactly what moved. Zero changes → the workflow quietly no-ops.

## 2. Architecture Map

| Component | Path | Role |
|---|---|---|
| Nightly workflow | `.github/workflows/nightly-readiness.yml` | cron 03:00 UTC → branch → PR |
| PR workflow | `.github/workflows/automated-readiness.yml` | per-PR doc refresh + comment |
| Legacy nightly | `.github/workflows/nightly.yml` | (kept for reference; superseded) |
| Orchestrator | `Makefile` | every script has a `make` target |
| Docs | `README_AUTOMATION.md`, `docs/GITHUB_ACTIONS_AUTOMATION.md` | human on-ramps |

Required permissions (both workflows):

```yaml
permissions:
  contents: write        # commit generated files
  pull-requests: write   # open PRs / comment
```

Optional secret: `PRODUCTION_URL` (defaults to `http://localhost:8000` so
metrics collection degrades gracefully instead of failing).

## 3. The Script Catalog

Every generator is idempotent, honors `SKIP_INTERACTIVE=true`, and is safe to
run on a CI runner with no human present. That flag convention is the single
most important design rule — it is what makes an interactive audit script
automatable.

| Script | `make` target | Output artifact | What it answers |
|---|---|---|---|
| `scripts/security-audit.sh` | `make security-audit` | `security-reports/` | bandit + dependency scan — any new CVE/hotspot? |
| `scripts/test-coverage-improvement.sh` | `make test-coverage` | `docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md` | where coverage fell, what to test next |
| `scripts/fill-dataroom-placeholders.py` | — | `docs/DATAROOM_FILL_GUIDE.md` | which investor-dataroom docs still have placeholders |
| `scripts/collect-metrics.sh` | `make metrics-collect` | `yc/METRICS_SNAPSHOT.md` | point-in-time product metrics |
| `scripts/calculate-unit-economics.py` | `make unit-economics` | `yc/UNIT_ECONOMICS.md` | CAC/LTV template state |
| `scripts/yc-application-checklist.sh` | `make yc-checklist` | `yc/YC_APPLICATION_CHECKLIST.md` | accelerator-application readiness |
| `scripts/get-users-checklist.sh` | — | user acquisition checklist | first-100-users plan freshness |
| `scripts/weekly-progress.sh` | `make weekly-progress` | `docs/WEEKLY_PROGRESS.md` | Mondays only: git log → narrative progress |
| `scripts/quick-start-readiness.sh` | `make readiness-check` | `readiness-report.txt` | composite go/no-go report |
| `scripts/env-doctor.py` | `make env-check` | — | env var / secret sanity |
| `scripts/doc-sync.py` | `make doc-sync` | — | docs ↔ code drift detector |
| `scripts/deploy-doctor.sh` | — | — | pre-deploy health gate |
| `scripts/smoke-tests.sh` | — | — | post-deploy endpoint checks |

CI hygiene targets (same Makefile): `make ci` = `lint` (ruff + black --check)
+ `type-check` (mypy) + `test-unit` (pytest, marks-excluded integration/e2e).

## 4. Workflow Anatomy (the parts that matter)

Both workflows share this skeleton — copy it verbatim for adoption:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0                      # need history for weekly-progress
- uses: actions/setup-python@v6
  with: { python-version: "3.11", cache: 'pip' }
- run: pip install -e ".[dev]" bandit safety jq
- run: |                                # bot identity = no self-PR loops
    git config --global user.name  "github-actions[bot]"
    git config --global user.email "github-actions[bot]@users.noreply.github.com"
- name: Run <audit>
  continue-on-error: true               # one broken audit must not kill the run
  env: { SKIP_INTERACTIVE: true }
  run: bash scripts/<audit>.sh || true
- name: Check for changes               # git diff --staged --quiet gate
- name: Commit + push                   # only if changed=true
- name: Create Pull Request             # actions/github-script@v7, dated branch
```

Non-obvious rules learned the hard way:

1. **`continue-on-error: true` + `|| true` on every audit step.** The nightly
   run exists to *report*, not to gate. A failing bandit check must still let
   the metrics snapshot commit. Gate on green CI in your *test* workflows,
   never in the reporter.
2. **Dated branch names** (`automated/nightly-readiness-updates-YYYYMMDD`)
   make retried runs idempotent (`git checkout -b ... || git checkout ...`).
3. **No-changes → no PR.** The `git diff --staged --quiet` check is the
   quiet-keeper. Without it you get 365 empty PRs a year and you start
   ignoring the system, which defeats the entire point.
4. **Bot git identity** prevents Actions-from-Actions recursion storms.

## 5. The Triage Loop (running your own PR avalanche)

The nightly PRs are the product. Treat them like an inbox, not noise.

**Daily (2 minutes):**

```bash
gh pr list --repo Hardonian/JupyterNotebooks --state open --limit 10
gh pr view <N> --repo Hardonian/JupyterNotebooks --json files,title   # what moved?
```

- Green + changes are just generated reports → merge.
- Security report shows a new finding → **do not merge blind**; fix first,
  the PR is a tripwire, not a deliverable.

**Bulk sweep (weekly, or when the pile gets >10):**
Use `gh pr merge --squash --delete-branch`, one PR at a time, **serially per
repo**. Dependabot and bot PRs share lockfiles; parallel merges in the same
repo race the base branch ("Base branch was modified"). GitHub also recomputes
`mergeable` asynchronously after every push — a PR that shows `UNKNOWN` is
*pending*, not broken: poll the REST API until `mergeable` resolves to
true/false before deciding. If `mergeable_state` is `dirty`, the conflict is
real; if `blocked`, branch protection is waiting on required checks.

One real sweep, one morning, 81 repos, verified via `mergedAt`: **42 PRs
merged, zero conflicts introduced.** The rest stayed open for a reason
(dirty / failing checks / branch policy) — the API never lies if you read the
right field.

**Housekeeping when nightly PRs stack up:** older dated nightly PRs usually
supersede each other (same generated files). Close the stale ones with a
comment, keep the newest — or let a scheduled cleanup job do it.

## 6. Failure Modes & Fixes

| Symptom | Root cause | Fix |
|---|---|---|
| Nightly silently stops | repo inactive 60 days → GitHub disables cron | `gh workflow run nightly-readiness.yml` (dispatch re-enables); alert on last-run age |
| PR never created | no changes / push denied by branch protection on `automated/*` | check `steps.changes` output in run log |
| Workflow loop storm | Actions committed with a non-bot identity or PAT | use `github-actions[bot]` config + default `GITHUB_TOKEN` |
| Audit step fails whole run | missing `continue-on-error` | add it (see §4.1) |
| `safety` 429s / flaky | free vulnerability DB rate limits | treat as advisory (`\|\| true`), move authoritative scanning to `pip-audit` + Dependabot |
| Merge says "base branch was modified" | concurrent merge to same repo | merge serially per repo, re-read PR, retry |
| `mergeable: null` forever | GitHub still recomputing | poll (5–30 s) before classifying as conflict |

## 7. Security Posture

- No secrets on the runner: scripts read `PRODUCTION_URL` from Actions
  secrets, everything else degrades to localhost defaults.
- `GITHUB_TOKEN` scoped to `contents: write, pull-requests: write` — least
  privilege for the loop; never `workflow: write` (that's how a compromise
  becomes persistent).
- Generated reports contain findings, not exploit material; bandit output is
  severity-tagged and lives in-repo intentionally (transparency for audits).
- Branch protection on `main` still gates what the bot PRs can merge.

## 8. Adoption Guide (port to any repo in ~1 afternoon)

1. Copy both workflow YAMLs; delete audits that don't apply to your stack.
2. Keep the three invariants: `SKIP_INTERACTIVE=true`, `continue-on-error`,
   no-changes-no-PR. They are the whole machine.
3. Add a `Makefile` with one target per script so local runs == CI runs.
4. Start with **two** audits you actually trust (e.g. security scan +
   doc-drift check). Grow the catalog only when a report proves it earns its
   nightly slot. Bloat here is how these systems die.
5. Schedule yourself a 5-minute inbox check or a bulk sweep timer (§5) for
   day 2 — an untriaged nightly PR pile becomes noise in a week.

## 9. Verification Commands (is the loop alive?)

```bash
# when did the loop last run end-to-end?
gh run list --repo Hardonian/JupyterNotebooks --workflow nightly-readiness.yml --limit 3
# trigger it right now
gh workflow run nightly-readiness.yml --repo Hardonian/JupyterNotebooks
# follow it
gh run watch
# what does the newest bot PR contain?
gh pr list --repo Hardonian/JupyterNotebooks --author "github-actions[bot]" --state open
```

---

## Appendix A — Timeline of This System

- v1: manual `make readiness-check` before investor emails (forgotten twice).
- v1.1: cron job on a laptop (dies on lid close — motivation for GH Actions).
- v2.0 (now): fully unattended nightly + per-PR automation, 14+ report
  generators, dated-branch PR workflow, zero maintenance between sweeps.

*The rule this repo lives by: a check that did not run must never report as
passed. The nightly PR is the proof it ran.*
