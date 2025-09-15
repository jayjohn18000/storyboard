Prompt 1 — Set shared context, guardrails, and task checklist

Objective: Give Cursor project-wide context + create a living checklist it will maintain.

Prompt to paste into Cursor:

You are acting as a senior integration engineer.

Create docs/LEGAL_SIM_ARCH.md and paste in the summary below (verbatim) so you can reference it.

Create docs/INTEGRATION_CHECKLIST.md with the following sections and checkboxes (leave them unchecked):

Phase 1: Service Communication (HTTP clients, discovery, retries, circuit breaker, health)

Phase 2: Database Integration (DatabaseService, repositories, sessions, Alembic)

Phase 3: Event Bus (Redis pub/sub), handlers, workflow orchestration, event sourcing stubs

Phase 4: Storage Integration (upload pipeline, WORM, chain of custody)

Policy Engine (OPA/Cerbos) middleware + mode enforcement

Observability (OTel traces/metrics, structured logs)

E2E Tests (happy path: upload → process → storyboard → timeline → render)

Add CONTRIBUTING.md with: small PRs, run make check, commit style: feat(scope): summary.

Create .cursor/rules.md with: always write minimal diffs, refuse sweeping refactors, prefer interfaces already present, preserve public API and env var names.

Add a root Makefile with targets: format, lint, test, up, down, e2e.
Architecture summary to paste into docs/LEGAL_SIM_ARCH.md:
(Paste the full “Legal Simulation Platform - Technical Architecture Overview” message you gave me.)

Accept when: files exist, checklist present, Makefile added.

Commit: docs: add architecture summary, checklist, contribution rules, and make targets

Prompt 2 — Config & service discovery scaffolding

Objective: Standardize per-service config + base URLs via env; no hardcoded localhost.

Prompt:

Create a shared config module used by all services: shared/config.py.

Read env for each service base URL:
API_GATEWAY_URL, EVIDENCE_URL, STORYBOARD_URL, TIMELINE_URL, RENDER_URL.

Provide get_service_url(name: Literal["evidence","storyboard","timeline","render"]) -> AnyUrl.

Validate ports (8000..8004 default).
Add .env.example with sensible defaults.
Replace any hardcoded http://localhost:8xxx with calls to get_service_url.
Add a /health FastAPI route in every service (returns {status:"ok", service:"<name>", time:<iso>}).

Accept when: no hardcoded URLs remain; all services expose /health and respond.

Commit: feat(config): shared service discovery via env + health endpoints

Prompt 3 — Shared HTTP client with retries and circuit breaker

Objective: Implement resilient inter-service HTTP calls.

Prompt:

Create shared/http_client.py using httpx.AsyncClient.

Add request_json(method, url, *, timeout=5, retries=3, backoff=0.25). Use tenacity for retry on 5xx/timeout.

Implement a simple in-memory circuit breaker (half-open after 30s).

Log request id, service name, latency, status code.
Add tenacity to requirements where needed.
Replace existing direct httpx/requests calls with request_json wrapper.

Accept when: transient failures retry; breaker opens after consecutive failures; logs include latency.

Commit: feat(http): resilient http client with retries and circuit breaker

Prompt 4 — Wire API Gateway → Evidence service (read paths only)

Objective: Replace mocks with real HTTP calls for list/get.

Prompt:

In API Gateway routes for Evidence, replace mock returns with real calls:

GET /evidence: call GET {EVIDENCE_URL}/evidence?filters=... → proxy response.

GET /evidence/{id}: call GET {EVIDENCE_URL}/evidence/{id}.
Add 2 integration tests in gateway: happy path and upstream 500 (verify 502 with error body).
Update OpenAPI docstrings consistently.

Accept when: gateway lists/gets evidence via HTTP in dev; tests pass.

Commit: feat(gateway): evidence list/get via HTTP instead of mocks

Prompt 5 — Database layer: sessions + repositories + Alembic

Objective: Make persistence real.

Prompt:

For each service with DB access (Evidence, Storyboard, Timeline), do the following:

Add db/session.py exposing SessionLocal, get_db() (yield context manager), engine, Base.

Add Alembic: alembic.ini, alembic/versions/ and an initial rev-0001_init.py generating tables for current SQLAlchemy models.

Implement repositories:

repositories/cases.py (CaseRepository)

repositories/evidence.py (EvidenceRepository)

repositories/storyboard.py (StoryboardRepository)
Each repository exposes CRUD + filter/query methods used by routes.

Update FastAPI routes to use Depends(get_db) and repositories (no ORM in routes).

Add make db-upgrade that runs Alembic migrations.

Accept when: migrations run clean; CRUD works locally; routes use repositories only.

Commit: feat(db): sessions, repositories, and Alembic migrations

Prompt 6 — Uploads that actually store files (Storage v1)

Objective: Connect evidence upload to real storage.

Prompt:

In Evidence service:

Implement storage/iface.py (interface), storage/local.py (local disk), with SHA256 hashing, size, MIME sniffing.

Route POST /evidence/upload:

stream to temp, compute hash, move to content-addressed path /data/evidence/<hash[0:2]>/<hash>

insert DB record (file meta, uploader, timestamps)

return record id + hash

Add virus scan hook placeholder (no-op now).

Enforce max size via env MAX_UPLOAD_MB.
Add tests: small file, duplicate upload (idempotent by hash).

Accept when: file lands on disk, DB row created, duplicates dedupe by hash.

Commit: feat(evidence): real upload pipeline with local storage and hashing

Prompt 7 — Chain of custody + WORM (minimal)

Objective: Track every touch; lock files after commit.

Prompt:

Add tables: chain_of_custody (evidence_id, action, actor, ts, metadata JSON) and evidence_lock (evidence_id, immutable_at).

On upload: record INGESTED.

Add endpoint POST /evidence/{id}/commit → sets immutable_at=now(), denies further writes, records LOCKED_WORM.

Enforce in repository: any write after immutable_at raises 409.
Add tests for lock behavior.

Accept when: writes after commit are rejected; custody entries created.

Commit: feat(storage): chain of custody and minimal WORM lock

Prompt 8 — Event bus (Redis) and event schemas

Objective: Start async comms.

Prompt:

Add events/models.py with Pydantic events: EvidenceUploaded, EvidenceProcessed, StoryboardCreated, TimelineCompiled, RenderCompleted.
Add events/bus.py implementing Redis pub/sub: publish(event), subscribe(event_type).
Wire Evidence service to publish(EvidenceUploaded) after successful upload/commit.
Create a lightweight consumer in Evidence Processor service that subscribes to EvidenceUploaded and logs receipt (no processing yet).
Add docker-compose service for Redis if not present.

Accept when: publishing works; processor logs incoming events.

Commit: feat(events): Redis pub/sub with typed event models

Prompt 9 — Processing workflow v1 (Evidence → Processor → DB → Storyboard)

Objective: Make results persist and flow.

Prompt:

In Evidence Processor:

On EvidenceUploaded, run dummy analysis (e.g., extract text via OCR stub or placeholder) and write results to its DB (evidence_analysis table).

Publish EvidenceProcessed with references.
In Storyboard service:

Subscribe to EvidenceProcessed, create a storyboard row linked to the case/evidence, status DRAFT.

Expose GET /storyboards/{id} and GET /cases/{id}/storyboards.
Add tests for event → DB side effects.

Accept when: uploading evidence leads to analysis row + storyboard row via events.

Commit: feat(workflow): basic evidence processing pipeline to storyboard

Prompt 10 — Policy engine middleware (Cerbos/OPA ready)

Objective: Enforce mode & RBAC at the edge.

Prompt:

Add policy/middleware.py used by all services:

Read POLICY_MODE in {disabled, rbac, cerbos} (default rbac).

For rbac: check JWT roles vs route annotations (add simple @requires("role")).

For cerbos: call PDP at CERBOS_ADDR with principal, resource, action; deny on fail.

Add SANDBOX vs DEMONSTRATIVE mode via env to block mutating routes when sandboxed.
Protect upload/commit/render endpoints accordingly.
Add unit tests for allow/deny.

Accept when: protected routes 403 without role; sandbox blocks mutating ops.

Commit: feat(policy): middleware with RBAC and Cerbos-ready hook

Prompt 11 — Timeline Compiler & Render Orchestrator wiring

Objective: Complete the service chain with real HTTP hops.

Prompt:

In Storyboard service: add POST /storyboards/{id}/compile → calls Timeline Compiler via shared HTTP client with storyboard payload; store compiled timeline id/status.
In Timeline Compiler: POST /timeline/compile → creates timeline artifacts and publish(TimelineCompiled).
In Render Orchestrator: subscribe to TimelineCompiled, start render job, persist render record and publish(RenderCompleted).
Expose GET /renders/{id} and GET /cases/{id}/renders.
Add gateway routes that call across services for compile & render.

Accept when: manual call to compile endpoint triggers timeline + render, with persisted rows.

Commit: feat(chain): storyboard→timeline→render end-to-end wiring

Prompt 12 — Observability (OTel) + structured logs + health/readiness

Objective: Trace cross-service calls and expose healthz/readyz.

Prompt:

Add OpenTelemetry instrumentation (FastAPI + httpx) in each service with service.name set. Export to stdout or OTLP if OTEL_EXPORTER_OTLP_ENDPOINT set.
Switch logging to JSON (timestamp, level, svc, route, req_id, latency).
Add /ready endpoints that verify DB + Redis connectivity.
Emit span attributes for case_id, evidence_id when present.

Accept when: traces show spans across services; readiness fails if DB/Redis down.

Commit: feat(obs): OpenTelemetry traces, JSON logs, readiness checks

Prompt 13 — E2E “happy path” test & Makefile plumbing

Objective: Lock in the full flow with a single test.

Prompt:

Create tests/e2e/test_happy_path.py that:

boots stack via docker-compose (or assumes running),

POST upload evidence via Gateway,

waits/polls until a render artifact appears (or RenderCompleted),

asserts DB rows created in each service,

asserts custody + WORM lock recorded.
Implement a tiny polling helper with timeout.
Wire make e2e to run this test.
Update docs/INTEGRATION_CHECKLIST.md to check completed items.

Accept when: make e2e passes locally.

Commit: test(e2e): upload→process→storyboard→timeline→render

Prompt 14 — Gateway OpenAPI & SDK generation

Objective: Clean API and provide a typed client.

Prompt:

Ensure the API Gateway aggregates OpenAPI schemas from downstream services (or publishes its own canonical API).
Add scripts/gen-sdk.sh using openapi-python-client to produce sdk/python/ for consumers.
Add CI check that schema builds.

Accept when: sdk/python/ builds; docs list endpoints clearly.

Commit: chore(api): canonical OpenAPI and Python SDK generation

Prompt 15 — Hardening: feature flags, rollbacks, and limits

Objective: Guardrails before prod-like usage.

Prompt:

Add simple feature flags via env for: ENABLE_EVENTS, ENABLE_RENDER, ENABLE_STORAGE_WORM.
Add request rate limits on upload/compile/render (per-IP token bucket; simple in-memory is fine for dev).
Document rollback: disable flags + revert to last migration tag.
Update docs/INTEGRATION_CHECKLIST.md and add a “Runbook.md” with failure modes and quick fixes.

Accept when: toggling flags disables features without changing code.

Commit: feat(flags): feature toggles + limits + runbook