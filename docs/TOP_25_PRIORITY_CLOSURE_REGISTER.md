# Top 25 Priority Closure Register

Updated: 2026-10-12. This is the authoritative in-repository priority register
for production readiness. “Complete” means source and automated evidence are
available; external validation still requires the linked closure gate.

| # | Priority | Current evidence | Closure state / next gate |
|---:|---|---|---|
| 1 | Secure production configuration | Startup validation rejects unsafe JWT, wildcard CORS, missing production DB, and debug mode. | External credentials gate |
| 2 | Authentication | JWT expiry, inactive-user rejection, and database-backed user lookup are tested. | Complete in repo |
| 3 | Authorization | RBAC is enforced on agent/tool/workflow/blueprint/execution/scheduler/referral routes. | Pilot permission review |
| 4 | Tool execution safety | Persisted tools bind only trusted runtime callables; API code execution is rejected. | Complete in repo |
| 5 | Safe expression evaluation | AST evaluator rejects import/eval/exec chains. | Complete in repo |
| 6 | Agent lifecycle | Registry persistence, hydration, execution records, and telemetry are tested. | Provider pilot gate |
| 7 | Workflow lifecycle | Deserialization, hydrated agents, start-step execution, retries, and status paths are tested. | Pilot workflow gate |
| 8 | Blueprint portability | Manifest, component JSON, secret-free env template, package/install behavior tested. | Pilot install gate |
| 9 | Shared API runtime | API routes share execution state for status, retry, and cancellation. | Complete in repo |
| 10 | Job queue selection | Deployment selects Redis or SQLite queue explicitly and rejects unsupported choices. | Queue-backend deployment test |
| 11 | Scheduler isolation | Scheduler owns its jobs, validates schedules, and supports targeted cancellation. | Durable schedule-storage decision |
| 12 | Webhook delivery | HTTPS validation, HMAC signing, retries, and audit events are tested. | Durable subscription storage gate |
| 13 | Provider resilience | OpenAI timeout/retry configuration, streaming, and safe tool-call JSON decoding are tested. | Real-provider smoke test |
| 14 | Anthropic adapter | Initialization and message response handling are tested. | Real-provider smoke test |
| 15 | Health/readiness | SQLAlchemy 2-compatible probes pass end-to-end. | Staging probe evidence |
| 16 | Telemetry | Event construction, storage, deserialization, and analytics compatibility are tested. | Retained production sink evidence |
| 17 | Audit trail | Mutation audit events and audit logger contract are tested. | Security retention review |
| 18 | Billing correctness | Plan defaults and non-duplicative execution/token metering are tested. | Stripe sandbox reconciliation |
| 19 | Marketplace/compliance | Search, compliance export, and retention paths have passing tests. | Data-governance approval |
| 20 | Export/import | Agent/workflow/blueprint definitions round-trip through a selected registry; no callable code imports. | Tenant-bound registry review |
| 21 | Enterprise SSO | Configuration validates secure endpoints, redacts secrets, and stays pending until IdP verification. | IdP login-round-trip gate |
| 22 | Referral integrity | Authenticated user/tenant ownership is enforced; cross-tenant access is tested. | Durable referral-store gate |
| 23 | Orchestration | Executor now runs actual agents and handles errors/step limits instead of fabricated output. | Multi-agent pilot scenario |
| 24 | Full regression suite | Release-candidate run on 2026-10-12: `uv run --extra dev pytest -q` — **301 passed, 3 skipped**. | Complete in repo |
| 25 | Release governance | [PROJECT_CLOSURE_GATES.md](PROJECT_CLOSURE_GATES.md) defines credential, security, ops, and pilot sign-off evidence. | External sign-offs required |

## Non-negotiable release rule

Items marked “external gate” are not completed by source code. The release
owner must attach the evidence defined in [PROJECT_CLOSURE_GATES.md](PROJECT_CLOSURE_GATES.md) before a production launch. This register must be
updated with the release-candidate test run and gate references at that time.
