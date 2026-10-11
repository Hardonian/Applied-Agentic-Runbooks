# Your Repo Should Open Its Own PR Every Night

### The Self-Auditing Repo Runbook — v2.1

**System:** `Hardonian/JupyterNotebooks` (Agent Factory) · **Operator:** Scott Hardie
**Stack:** 2 GitHub Actions workflows · 16 audit generators · 1 Makefile
**Track record:** 320 consecutive nightly runs — 320/320 green, zero gaps,
Nov 26 2025 → Oct 11 2026, every one cron-triggered (verified via the
Actions API run log: `workflow_runs?event=schedule`).
**Last verified:** 2026-10-11

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
| Silence = fine | No PR = loop died (see §7 failure matrix) |

A PR is the perfect accountability primitive: it has an author, a timestamp,
a diff, and it will not close itself.

## 2. Architecture: The Loop

```
            ┌──────────────────────────────────────────────┐
            │                                              │
  03:00 UTC │  GitHub Actions (nightly-readiness.yml)      │
      ─────►│   1. checkout main                           │
            │   2. run every audit script (non-interactive)│
            │   3. git add -A; diff --staged --quiet?      │
            │      ├─ no changes → exit silently            │
            │      └─ changes   → dated branch → commit ────┤
            │   4. open PR "🤖 Nightly Readiness - <date>"  │
            └──────────────┬───────────────────────────────┘
                           │
                     THE INBOX  ◄── your entire "maintenance" job
                           │
        ┌──────────────────┴───────────────────┐
        │ boring report → squash-merge         │
        │ new finding   → FIX FIRST, then merge│
        │ PR missing    → incident (§7)        │
        └──────────────────────────────────────┘
```

A second workflow (`automated-readiness.yml`) runs the same audits on every
PR and push to `main`, committing refreshed docs straight onto the branch and
posting a summary comment. The nightly PR is the heartbeat; the PR workflow
is the reflex arc.

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

**Invariant 3 — No changes, no PR (`git diff --staged --quiet`).**
Without this you get 365 empty PRs a year, you start ignoring the inbox in
week two, and the system is dead with a pulse. With it, **the presence of a
PR is itself the alert** and absence means the audit had nothing new to say.

## 4. Copy-Paste Skeleton (the YAML that matters)

```yaml
name: Nightly Readiness Updates
on:
  schedule: [{cron: '0 3 * * *'}]
  workflow_dispatch:            # ← also your "is it alive" test button
permissions:
  contents: write               # least privilege — never workflow: write
  pull-requests: write

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
          git add -A
          git diff --staged --quiet || echo "changed=true" >> $GITHUB_OUTPUT

      - name: Commit + dated branch + PR
        if: steps.changes.outputs.changed == 'true'
        # branch: automated/nightly-readiness-updates-YYYYMMDD
        # → idempotent retries; PR via actions/github-script@v7
```

## 5. The Audit Catalog (what actually runs nightly here)

The nightly job runs 7 audits; the per-PR job runs 9 (two extra
checklists); 16 generators total have `make` targets so **local run ==
CI run**. Full catalog:

| Nightly audit | Command | Artifact it maintains |
|---|---|---|
| Security scan | `make security-audit` | `security-reports/` (bandit + deps) |
| Coverage gap plan | `make test-coverage` | `docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md` |
| Doc↔code drift | `make doc-sync` | drift report / synced stubs |
| Env/secret sanity | `make env-check` | — |
| Readiness composite | `make readiness-check` | `readiness-report.txt` |
| Metrics snapshot | `make metrics-collect` | `yc/METRICS_SNAPSHOT.md` |
| Unit economics | `make unit-economics` | `yc/UNIT_ECONOMICS.md` |
| Dataroom placeholders | `scripts/fill-dataroom-placeholders.py` | `docs/DATAROOM_FILL_GUIDE.md` |
| Fundraise checklist | `make yc-checklist` | `yc/YC_APPLICATION_CHECKLIST.md` |
| Weekly progress (Mondays) | `make weekly-progress` | `docs/WEEKLY_PROGRESS.md` |
| Deploy doctor | `scripts/deploy-doctor.sh` | pre-deploy gate report |
| Smoke tests | `scripts/smoke-tests.sh` | post-deploy endpoint proof |
| …plus acquisition + user checklists | | |

Design rule for the catalog: **a report earns its nightly slot by being read
at least once a month.** When one stops getting opened, delete it. Catalog
bloat is how these systems die — not outages.

## 6. The Triage Loop (your 2-minute job)

The PRs are the product. Treat them like a mail queue, not a backlog.

```bash
gh pr list --repo OWNER/REPO --author "github-actions[bot]" --state open
gh pr view N --json files,title       # what moved overnight?
```

- **Boring report refresh** → squash-merge.
- **Security report that changed** → tripwire, not deliverable. Fix first.
- **No PR for >2 nights with activity expected** → incident (§7 row 1).

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
| 1 | Loop stops silently | GitHub disables cron on repos inactive 60 days | `gh workflow run` (dispatch re-enables); alert on last-run age |
| 2 | Run green, no PR | `changed=false` (normal) or push denied by branch protection | check the gate step output once, then trust it |
| 3 | Actions spawn-Actions storm | committed as human/PAT identity | bot git identity + default `GITHUB_TOKEN` |
| 4 | One audit kills the run | missing `continue-on-error` | Invariant 2 |
| 5 | `safety` flaky/429 | free vuln-DB rate limits | advisory only; Dependabot + `pip-audit` are authoritative |
| 6 | "Base branch was modified" | concurrent merges in same repo | merge serially per repo; re-read PR; retry |
| 7 | `mergeable: null` forever | recompute pending | poll 5–30 s before classifying |
| 8 | Nightly PRs pile up >2 wks | nobody triaged | inbox timer or bulk sweep — or you built a notification farm, not a system |

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

## 9. The Verification Doctrine

This system exists because of one unforgivable pattern in engineering:
**a check that did not run reporting as passed.**

- Every claim about repo health must trace to a run id + timestamp.
- Every merge claim must trace to `mergedAt` read back from the API.
- The nightly PR *is* the proof-of-life. No PR, no pulse, page yourself.

The repo doesn't need you to believe it's production-ready. It files the
evidence every night at 03:00 UTC and waits for you to merge it.

---

### TL;DR for the README of your repo

```
This repo audits itself. Every night at 03:00 UTC it runs security,
coverage, docs, and metrics audits, and opens a PR with whatever changed.
No PR means nothing changed. Missing PRs mean something broke — see
docs/RUNBOOK.md. The loop is the proof.
```

*Changelog: v2.1 (2026-10-11) — verification doctrine, invariants framing,
exact verified field data (320-night streak via run log; 81-repo scan /
105-PR classify / 47-merge sweep via mergedAt+mergedBy), adoption sequencing.
v2.0 — original comprehensive runbook. v1 — scripts on a laptop, cron under a
lid (the dark ages).*
