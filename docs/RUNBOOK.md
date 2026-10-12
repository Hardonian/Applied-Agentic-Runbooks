# Your Repo Should Open Its Own PR Every Night

### The Self-Auditing Repo Runbook — v2.2

**System:** `Hardonian/JupyterNotebooks` (Agent Factory) · **Operator:** Scott Hardie
**Stack:** 2 readiness workflows · 9 audit/report generators · 1 Makefile
**Historical track record:** 320 consecutive nightly runs — 320/320 green,
zero gaps, Nov 26 2025 → Oct 11 2026, every one cron-triggered (recorded
from the Actions API run log: `workflow_runs?event=schedule`).
**Configuration verified:** Run `make verify-runbook` locally or in CI. The
historical streak must be rechecked from GitHub before it is extended.
**Liveness verified:** Run `make check-readiness-heartbeat` from an external
monitor with a GitHub token that can read Actions runs.

---

> Every repo claims to be "production-ready." Almost none can prove it on
> Tuesday at 3am. This one proves it to itself, every night, and files the
> receipts as a pull request.
>
> You don't get to be the person who "keeps docs up to date." That person
> does not exist. Not on your team, not in your future, not in yours. The
> loop below replaces that person, and it has run 320 nights in a row without
> me touching it.
>
> This is not theory. This is the actual system, the actual YAML, the actual
> failure modes, and an afternoon-sized adoption guide. Copy it. Argue with
> it later.

---

## 0. The One-Sentence Pitch

**A repo that audits itself nightly — security, coverage, docs, metrics — and
opens its own PR with the results, turning "project health" from a vibe into
an inbox.**

## 1. Why This Exists (the honest version)

The standard stack fails at one specific place: **the gap between "we have
scripts" and "someone ran them."**

- CI gates *block*. Nobody fixes a red gate at 2am; they hit re-run or merge
  anyway. Gating teaches avoidance.
- Dashboards *sit*. A green tile on a board nobody opens is a lie with
  better pixels.
- Manual audits *decay*. The checklist you wrote in March is fiction by June.

The self-auditing repo inverts all three:

| Old instinct | This system |
|---|---|
| Health is a dashboard | Health is a pull request |
| Checks block merges | Checks *report*; humans gate |
| Docs get stale, someone notices someday | The nightly run *rewrites* the stale parts and shows its diff |
| Silence = fine | A successful scheduled workflow run proves liveness; a PR proves changed output |

A PR is the perfect accountability primitive: it has an author, a timestamp,
a diff, and it will not close itself.

## 2. Architecture: The Loop

```
            ┌──────────────────────────────────────────────┐
            │                                              │
  03:00 UTC │  GitHub Actions (nightly-readiness.yml)      │
      ─────►│   1. checkout main                           │
            │   2. run every audit script (non-interactive)│
            │   3. stage allowlisted artifacts; diff?      │
            │      ├─ no changes → exit silently            │
            │      └─ changes   → dated branch → commit ────┤
            │   4. open PR "🤖 Nightly Readiness - <date>"  │
            └──────────────┬───────────────────────────────┘
                           │
                     THE INBOX  ◄── changed-output review
                           │
        ┌──────────────────┴───────────────────┐
        │ boring report → squash-merge         │
        │ new finding   → FIX FIRST, then merge│
        │ heartbeat fails → incident (§7)      │
        └──────────────────────────────────────┘
```

A second workflow (`automated-readiness.yml`) runs the overlapping readiness
generators on every PR and push to `main` or `develop`, then publishes the
result as a workflow summary and PR comment. It is deliberately **report-only**:
it never writes to a contributor or protected branch. The nightly PR is the
heartbeat; the PR workflow is the reflex arc.

An external heartbeat monitor is the watchdog. It queries the Actions API for
the most recent **scheduled** run and fails if that run is unsuccessful or
older than the agreed threshold. A PR cannot prove liveness: a healthy audit
with no changed artifact correctly creates no PR.

## 3. The Three Invariants (memorize these)

The whole machine rests on three rules. Break one and you either get silence,
noise, or a dead loop.

**Invariant 1 — `SKIP_INTERACTIVE=true` everywhere.**
Every audit script must run with zero human prompts. This one convention is
the difference between "a tool we have" and "a system that runs." Any script
that asks a question is not automatable; fix the script, not the schedule.

**Invariant 2 — Report, don't gate (`continue-on-error: true` + `|| true`).**
The nightly workflow exists to *tell you things*, never to *block anything*.
One throwing audit must not silence the rest of them. Green
gating belongs in your test pipeline; the reporter's only job is to show up
with the receipts.

**Invariant 3 — No changed approved artifact, no PR (`git diff --staged --quiet`).**
Without this you get 365 empty PRs a year, you start ignoring the inbox in
week two, and the system is dead with a pulse. With it, **the presence of a
PR means a reviewable artifact changed. Absence is inconclusive; use the
heartbeat to verify that the scheduled run occurred.

**Invariant 4 — Audits may write only to an explicit artifact allowlist.**
The workflow stages the known report paths via
`scripts/stage-readiness-artifacts.sh`; it never uses `git add -A`. A failed,
compromised, or simply buggy audit therefore cannot turn arbitrary repository
changes into a bot-authored commit.

## 4. Copy-Paste Skeleton (the YAML that matters)

```yaml
name: Nightly Readiness Updates
on:
  schedule: [{cron: '0 3 * * *'}]
  workflow_dispatch:            # ← also your "is it alive" test button
permissions:
  contents: write               # least privilege — never workflow: write
  pull-requests: write

concurrency:
  group: nightly-readiness-${{ github.ref }}
  cancel-in-progress: false   # retries update the same dated PR serially

jobs:
  nightly:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}                # history for git-log audits
      - uses: actions/setup-python@v6
        with: {python-version: "3.11", cache: 'pip'}
      - run: pip install -e ".[dev]" bandit safety jq
      - run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
        # bot identity = no Actions-spawn-Actions recursion storm

      - name: Audit (repeat per script)
        continue-on-error: true
        env: {SKIP_INTERACTIVE: true}
        run: bash scripts/security-audit.sh || true

      - name: Gate on change
        id: changes
        run: |
          bash scripts/stage-readiness-artifacts.sh
          git diff --staged --quiet || echo "changed=true" >> $GITHUB_OUTPUT

      - name: Commit + dated branch + upsert PR
        if: steps.changes.outputs.changed == 'true'
        # branch: automated/nightly-readiness-updates-YYYYMMDD
        # → idempotent retries; update an existing PR before creating another
```

## 5. The Audit Catalog (what actually runs nightly here)

The nightly job runs 7 audits. The PR/push job runs those core reports plus
the YC and user-acquisition checklists (weekly progress runs only on Monday),
for 9 distinct generators. Each has a `make` target, so **local run == CI
run**. Full scheduled catalog:

| Nightly audit | Command | Artifact it maintains |
|---|---|---|
| Security scan | `make security-audit` | `security-reports/security_audit_summary_current.md` (raw details: 30-day CI artifact) |
| Coverage gap plan | `make test-coverage` | `docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md` |
| Dataroom placeholders | `make dataroom-placeholders` | `docs/DATAROOM_FILL_GUIDE.md` |
| Metrics snapshot | `make metrics-collect` | `yc/METRICS_SNAPSHOT.md` |
| Unit economics | `make unit-economics` | `yc/UNIT_ECONOMICS.md` |
| Weekly progress (Mondays) | `make weekly-progress` | `docs/WEEKLY_PROGRESS.md` |
| Readiness composite | `make readiness-check` | `readiness-report.txt` |

The PR/push workflow additionally runs `make yc-checklist` and `make
user-acquisition`. Deployment checks (`make deploy-doctor`, `make
smoke-tests`) remain explicit, target-environment operations; they do not run
in the nightly reporter.

## 5.1 Trust Boundary, Data Handling, and Retention

This system deliberately separates **collection** from **authority**:

- The nightly workflow is the only automated writer, and it has only
  `contents: write` and `pull-requests: write` permissions.
- The PR/push workflow is report-only (`contents: read`). It must never use
  `pull_request_target`, secrets from an untrusted fork, or a token that can
  write to the contributor branch.
- `scripts/stage-readiness-artifacts.sh` is the commit boundary. Add a path
  only after deciding that its contents are safe to retain in Git and safe for
  a reviewer to merge.
- Reports must contain no credentials, customer prompts, raw production data,
  or full request/response bodies. Put sensitive forensic output in a
  access-controlled incident system with an expiry, not in a PR.
- Keep committed summaries small and deterministic. Retain verbose scan logs
  as CI artifacts for a defined period (for example, 30 days) and link their
  run ID from the summary.

Treat generated text as untrusted input. It can recommend a command; it does
not get to execute one. A reviewer owns the decision to merge it.

## 5.2 Service Objectives and Ownership

| Signal | Objective | Owner action when missed |
|---|---|---|
| Scheduled readiness liveness | Latest scheduled run succeeds and is <30 hours old | Page the workflow owner; dispatch once, then repair the trigger or permissions |
| Changed-output review | Open bot PR triaged by next business day | Merge routine reports or file a named remediation issue |
| Security finding | Critical/high finding acknowledged within one business day | Stop routine merge; assign a security owner and mitigation deadline |
| Runbook contract | Passes on every push and pull request | Fix documentation/configuration drift before merge |

Name a primary owner and backup in the repository settings or `ON_CALL.md`.
Automation without an accountable human is merely scheduled output.

Design rule for the catalog: **a report earns its nightly slot by being read
at least once a month.** When one stops getting opened, delete it. Catalog
bloat is how these systems die — not outages.

## 6. The Triage and Liveness Loop (your 2-minute job)

The PRs are the product. Treat them like a mail queue, not a backlog.

```bash
gh pr list --repo OWNER/REPO --author "github-actions[bot]" --state open
gh pr view N --json files,title       # what moved overnight?
GITHUB_TOKEN=... make check-readiness-heartbeat
```

- **Boring report refresh** → squash-merge.
- **Security report that changed** → tripwire, not deliverable. Fix first.
- **Heartbeat fails** → incident immediately; it is the liveness signal.
- **No PR with a healthy heartbeat** → normal when no approved artifact
  changed. Do not manufacture a PR just to make the dashboard feel alive.

**Weekly bulk sweep** (this is where it stops being cute):

```bash
# serial per repo — parallel bot merges race the same base branch
gh pr merge N --repo OWNER/REPO --squash --delete-branch
```

Field-tested 2026-10-11: swept **81 active repos in one morning — 105 open
PRs classified, 47 non-conflicting green ones squash-merged, zero conflicts
introduced — every merge verified by reading `mergedAt` + `mergedBy` back
from the API.** The two API truths that made it work:

1. `mergeable: null` / `UNKNOWN` means *GitHub is still recomputing*, not
   *conflict*. Poll until it resolves — most "conflicts" evaporate.
2. `mergeable_state: dirty` is a real conflict; `blocked` is branch
   protection waiting on required checks. Different triage, never "retry
   until green."

## 7. Failure-Mode Matrix (each one has actually happened)

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | Loop stops silently | GitHub disables cron on repos inactive 60 days | `gh workflow run` (dispatch re-enables); external heartbeat alerts on last-run age |
| 2 | Run green, no PR | `changed=false` (normal) or push denied by branch protection | check the gate step output once, then trust it |
| 3 | Actions spawn-Actions storm | committed as human/PAT identity | bot git identity + default `GITHUB_TOKEN` |
| 4 | One audit kills the run | missing `continue-on-error` | Invariant 2 |
| 5 | `safety` flaky/429 | free vuln-DB rate limits | advisory only; Dependabot + `pip-audit` are authoritative |
| 6 | "Base branch was modified" | concurrent merges in same repo | merge serially per repo; re-read PR; retry |
| 7 | `mergeable: null` forever | recompute pending | poll 5–30 s before classifying |
| 8 | Nightly PRs pile up >2 wks | nobody triaged | inbox timer or bulk sweep — or you built a notification farm, not a system |
| 9 | Unexpected file appears in bot PR | an audit wrote outside its contract | confirm only allowlisted paths are staged; quarantine the audit and rotate credentials if exposure is possible |
| 10 | PR audit cannot comment | fork token is read-only or PR has no write permission | expected for untrusted forks; retain the workflow summary and never elevate to `pull_request_target` |
| 11 | Heartbeat is green but reports are stale | generator succeeded without producing a changed signal | inspect artifact timestamps/content; add a semantic assertion to that generator |
| 12 | Report contains sensitive data | over-broad telemetry or unredacted scan output | remove the committed artifact, rotate affected secrets, preserve evidence in restricted storage, and add a redaction test |

## 8. Adoption Guide — one afternoon, in order

1. **Day-zero, hour-one:** port *two* audits you actually trust (security +
   doc-drift are the classics). Not fifteen. Two.
2. Copy the §4 skeleton verbatim. Keep all three invariants. They are the
   machine; the audits are just cargo.
3. Give every script a Makefile target so `make security-audit` works on
   your laptop and on the runner identically.
4. Add the no-changes-no-PR gate **before your first test run**, not after
   the noise starts.
5. `gh workflow run` on day one; check `gh run list` on day two. The loop
   being *provably alive* is the feature.
6. After 2 weeks, add audits only when a specific question recurs ("did
   coverage drop again?"). The catalog should grow like scar tissue, not
   like graffiti.
7. Run `make verify-runbook` whenever the workflows or this runbook change.
   It checks the scheduled trigger, safety invariants, no-change gate,
   report-only PR workflow, and local command contract without GitHub access.
8. Configure `make check-readiness-heartbeat` in an **external** monitor (a
   scheduled job outside this repository, or a monitoring service). Give it a
   minimally scoped token that can read Actions runs and alert the named owner
   after 30 hours without a successful scheduled run.
9. Run one game day before declaring the system operational: force a changed
   artifact, simulate a failed audit, verify the PR and heartbeat behavior,
   then record the evidence and restore the baseline.

## 9. The Verification Doctrine

This system exists because of one unforgivable pattern in engineering:
**a check that did not run reporting as passed.**

- Every claim about repo health must trace to a run id + timestamp.
- Every merge claim must trace to `mergedAt` read back from the API.
- The latest successful **scheduled workflow run** is proof-of-life; check it
  through the Actions API, not by inferring from a PR.
- The bot PR is proof that an approved artifact changed and that a human now
  has a reviewable decision to make.
- A game-day record, run ID, timestamp, and responsible reviewer are the
  closure evidence for a change to this system.

The repo doesn't need you to believe it's production-ready. It files the
evidence every night at 03:00 UTC and waits for you to merge it.

## 10. Release Closure: Prove the Artifact, Not the Checkout

Nightly readiness reports answer, “is the repository being watched?” A
release answers a different question: **“is this exact distributable safe to
ship?”** Do not treat a green branch or a source-tree test run as release
evidence. The release candidate is the version tag and the built wheel/source
archive attached to it.

### Release gate sequence

```
version + changelog
        │
        ▼
metadata verification ──► non-integration tests
        │                         │
        └──────────┬──────────────┘
                   ▼
          build wheel + sdist
                   │
          ┌────────┴────────┐
          ▼                 ▼
 isolated wheel install   dependency audit + SBOM
          │                 │
          └────────┬────────┘
                   ▼
          live API product-path E2E
                   │
                   ▼
         GitHub Release (tagged only)
```

The `.github/workflows/release.yml` workflow enforces this sequence for every
`v*` tag. It must not publish a release if any dependency audit, artifact
check, or E2E job fails.

### What the live product-path E2E proves

The release E2E job starts the API from the **built wheel**, not an editable
checkout, on a disposable SQLite database. It verifies all of the following
over HTTP:

- An unauthenticated request is denied.
- A new user can sign up and retrieve their profile with the issued JWT.
- That user can create and list an agent.
- That user can create, list, and inspect a workflow referencing that agent.
- `/live`, `/ready`, `/health`, docs, OpenAPI, metrics, and concurrency
  behavior remain available.

The E2E client only connects to a live server when `API_BASE_URL` is explicitly
set, and it verifies that the endpoint identifies as Agent Factory before
running mutations. With no explicit URL, local tests use an in-process ASGI
client. This prevents a stray service on port 8000 from producing false green
or misleading red results.

The test deliberately does not call an external LLM. Provider-backed agent
execution, SSO, payment, webhook, and production-storage checks still require
the credentials and environment evidence in `PROJECT_CLOSURE_GATES.md`; they
are release holds when those capabilities are enabled.

### Operator procedure

1. Update `pyproject.toml`, `agent_factory.__version__`, and `CHANGELOG.md`.
2. Run `make verify-release`, the full test suite, and `make package-check`.
3. Review the dependency audit and `release-sbom` workflow artifact; resolve
   or formally accept any finding before tagging.
4. Commit the candidate, create an annotated `vX.Y.Z` tag, and push that tag.
5. Attach workflow run links and the SBOM to `RELEASE_EVIDENCE_RECORD.md`.
6. Complete the credential, security, operational, and pilot gates. Automation
   is evidence, never a substitute for the named human approvals.

### Release failure matrix

| Failure | Meaning | Required response |
|---|---|---|
| Metadata/tag mismatch | Candidate is ambiguous | Correct version or tag; rebuild from a clean commit |
| Wheel install fails | Artifact is not consumable | Hold release; fix package metadata or dependencies |
| Authenticated E2E fails | Core product path regressed | Hold release; fix and re-run against a new artifact |
| Dependency audit fails | Known vulnerable dependency | Upgrade, mitigate, or record time-bounded security exception |
| SBOM missing | Supply-chain evidence incomplete | Re-run the release workflow; do not manually publish |
| External-provider gate missing | Production capability unproven | Keep decision as HOLD until owner attaches evidence |

---

### TL;DR for the README of your repo

```
This repo audits itself. Every night at 03:00 UTC it runs security,
coverage, docs, and metrics audits, and opens a PR with whatever changed.
No PR normally means no approved artifact changed. A separate Actions API
heartbeat proves the nightly loop is alive — see docs/RUNBOOK.md.
```

*Changelog: v2.4 (2026-10-12) — release closure added: tag-gated metadata,
built-artifact install, authenticated product-path E2E, dependency audit, SBOM,
and an explicit boundary between automated evidence and human approval. v2.3
(2026-10-12) — best-in-class operational closure: explicit
artifact allowlist, external API heartbeat checker, trust/data-retention
boundary, SLOs and ownership, game-day procedure, and corrected PR-versus-
liveness semantics. v2.2 (2026-10-12) — closed workflow/documentation drift: exact
7-nightly/9-total generator catalog, report-only PR workflow, idempotent
nightly PR upsert, serial concurrency, and a local `make verify-runbook`
contract check. v2.1 (2026-10-11) — verification doctrine, invariants framing,
exact verified field data (320-night streak via run log; 81-repo scan /
105-PR classify / 47-merge sweep via mergedAt+mergedBy), adoption sequencing.
v2.0 — original comprehensive runbook. v1 — scripts on a laptop, cron under a
lid (the dark ages).*
