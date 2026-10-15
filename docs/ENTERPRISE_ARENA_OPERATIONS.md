# Enterprise Arena Operations

## Runtime architecture

Production clients submit work to `POST /api/v1/arena/jobs`. The API records the job
before scheduling execution and returns `202`, a status URL, and a run-specific event
topic. PostgreSQL is authoritative for lifecycle state and Redis Streams distributes
versioned events between replicas. The synchronous `/run` endpoint remains for CI and
backward compatibility.

Each completed job persists `.apcap`, VeriDAG, and signed manifest files beneath
`ARENA_ARTIFACT_DIR`. Set `ARENA_EVIDENCE_SIGNING_KEY` to an organizational secret and
verify exported bundles with `agent-factory arena verify MANIFEST`.

## Required production secrets

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `MCPWALL_APPROVAL_SIGNING_KEY`
- `ARENA_EVIDENCE_SIGNING_KEY`
- any configured local or cloud model credentials

Approval and evidence signing keys should be distinct, rotated through the platform’s
secret manager, and never supplied through Helm values committed to source control.

## Operational checks

1. Confirm `/live`, `/ready`, and `/metrics` before admitting traffic.
2. Submit a deterministic single-suite job and follow its `Location` header.
3. Reconnect to `/api/v1/ws/arena?topic=arena:<run-id>&cursor=<sequence>` and confirm
   missed events replay.
4. Download the three evidence artifacts and run offline verification.
5. Run `scripts/arena-soak.py` before promotion and after Redis/PostgreSQL upgrades.

## Failure and recovery

- A pod loss does not erase lifecycle state. Redis claims use a visibility lease;
  expired running jobs are automatically requeued up to their retry budget. Tune the
  lease with `JOB_VISIBILITY_TIMEOUT_SECONDS` (default: 1200).
- Redis loss pauses cross-pod delivery. Local bounded delivery continues, and clients
  reconcile against the durable status endpoint after reconnecting.
- PostgreSQL loss causes readiness to fail. Kubernetes removes the pod from service;
  no job is accepted without first persisting its record.
- Cancellation is cooperative at suite boundaries, preventing partial ledger state
  from being reported as complete.
- Evidence retention defaults to 30 days (`ARENA_RETENTION_DAYS`). Multi-replica Helm
  deployments require an RWX storage class unless an external artifact store is used.

## Security model

MCPWall tickets are tenant-bound, SHA-256-bound, TTL-limited, single-use records.
Operator decisions require an `operator`, `security`, or `admin` role, and requesters
cannot approve their own operations. Receipts are HMAC-signed and retained with the
ticket audit record. WebSocket origins are allowlisted with `WS_ALLOWED_ORIGINS`.

## Upgrade and rollback

The Helm pre-install/pre-upgrade migration Job applies Alembic migrations before new
pods start. Back up PostgreSQL and artifact storage before upgrades. Application
rollback is safe while schema revision 004 remains installed; its tables are additive.
Database downgrade is destructive and should be used only after exporting Arena and
approval audit records.
