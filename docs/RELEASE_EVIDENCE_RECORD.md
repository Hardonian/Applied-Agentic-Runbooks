# Release Evidence Record

Copy this record into the release/change ticket for every production candidate.
Use references, dates, and anonymized identifiers only. Never paste credentials,
tokens, customer content, or other secrets into this file or the ticket.

## Release identity

- Release/version:
- Commit or immutable build identifier:
- Environment and region:
- Change ticket:
- Release owner:
- Proposed release time (UTC):
- Rollback owner and target build:

## Repository evidence

- [ ] Full test result: `uv run --extra dev pytest -q`
- [ ] Result and timestamp: 301 passed, 3 skipped on 2026-10-12 (replace for
  a later candidate)
- [ ] `git diff --check` result:
- [ ] Dependency/security scan reference:
- [ ] Build artifact/provenance reference:

## Credential and deployment gate

- [ ] Secret-manager version references (no values):
- [ ] Database migration/init evidence:
- [ ] Explicit HTTPS CORS configuration verified:
- [ ] Provider credential smoke-test reference:
- [ ] Optional Stripe/webhook/observability/storage integrations validated:
- [ ] SSO IdP login-round-trip result, if enabled:
- Platform operator name/date:

## Security and compliance gate

- [ ] Pilot roles and API scopes reviewed:
- [ ] Mutation audit sink and retention verified:
- [ ] Data-retention, export, privacy, and incident obligations reviewed:
- [ ] Security/LLM scan findings disposition:
- [ ] Threat-model/residual-risk approval reference:
- Security approver name/date:

## Operational readiness gate

- [ ] Staging deployment and `/live`, `/ready`, `/health` evidence:
- [ ] Database and blueprint backup/restore drill:
- [ ] Rollback drill and measured rollback time:
- [ ] Alerts, on-call, rate limits, and error tracking configured:
- Service owner name/date:

## Pilot gate

- [ ] Pilot tenant/data classification/consent reference:
- [ ] External-provider integration scenarios completed:
- [ ] Agent run, workflow run, retry, cancellation, and blueprint install exercised:
- [ ] Audit, telemetry, costs, failure handling, and user feedback reviewed:
- [ ] Success criteria and observed metrics attached:
- [ ] Sponsor go/no-go decision:
- Product owner and sponsor names/dates:

## Release decision

- Decision: `GO` / `HOLD` / `ROLL BACK`
- Exceptions accepted (ticket references and expiry):
- Final approver and timestamp (UTC):
- Post-release verification time and owner:

The release is a **HOLD** unless all applicable entries above and every gate in
[PROJECT_CLOSURE_GATES.md](PROJECT_CLOSURE_GATES.md) are complete.
