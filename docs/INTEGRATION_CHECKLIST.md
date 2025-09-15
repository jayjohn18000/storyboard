# Legal Simulation Platform - Integration Checklist

This checklist tracks the integration phases for the Legal Simulation Platform. Check off items as they are completed.

## Phase 1: Service Communication (HTTP clients, discovery, retries, circuit breaker, health)

- [ ] Create shared config module (`shared/config.py`)
- [ ] Implement service discovery via environment variables
- [ ] Add health endpoints to all services (`/health`)
- [ ] Create shared HTTP client with retries (`shared/http_client.py`)
- [ ] Implement circuit breaker pattern
- [ ] Replace hardcoded URLs with service discovery
- [ ] Add request/response logging with correlation IDs
- [ ] Test service-to-service communication

## Phase 2: Database Integration (DatabaseService, repositories, sessions, Alembic)

- [ ] Set up database sessions (`db/session.py`)
- [ ] Create Alembic configuration and initial migration
- [ ] Implement CaseRepository (`repositories/cases.py`)
- [ ] Implement EvidenceRepository (`repositories/evidence.py`)
- [ ] Implement StoryboardRepository (`repositories/storyboard.py`)
- [ ] Update FastAPI routes to use repositories
- [ ] Add database health checks
- [ ] Test CRUD operations across services

## Phase 3: Event Bus (Redis pub/sub), handlers, workflow orchestration, event sourcing stubs

- [ ] Set up Redis pub/sub infrastructure
- [ ] Create event models (`events/models.py`)
- [ ] Implement event bus (`events/bus.py`)
- [ ] Add EvidenceUploaded event publishing
- [ ] Create Evidence Processor event consumer
- [ ] Add EvidenceProcessed event publishing
- [ ] Create Storyboard service event consumer
- [ ] Add TimelineCompiled event publishing
- [ ] Create Render Orchestrator event consumer
- [ ] Add RenderCompleted event publishing
- [ ] Test end-to-end event flow

## Phase 4: Storage Integration (upload pipeline, WORM, chain of custody)

- [ ] Implement storage interface (`storage/iface.py`)
- [ ] Create local storage implementation (`storage/local.py`)
- [ ] Add SHA256 hashing for content addressing
- [ ] Implement file upload pipeline
- [ ] Add chain of custody tracking
- [ ] Implement WORM (Write-Once, Read-Many) locking
- [ ] Add evidence commit endpoint
- [ ] Enforce immutable evidence after commit
- [ ] Test file upload and custody tracking

## Policy Engine (OPA/Cerbos) middleware + mode enforcement

- [ ] Create policy middleware (`policy/middleware.py`)
- [ ] Implement RBAC (Role-Based Access Control)
- [ ] Add Cerbos integration hooks
- [ ] Implement SANDBOX vs DEMONSTRATIVE mode enforcement
- [ ] Add route-level authorization annotations
- [ ] Protect mutating endpoints (upload/commit/render)
- [ ] Test authorization policies
- [ ] Add policy configuration management

## Observability (OTel traces/metrics, structured logs)

- [ ] Add OpenTelemetry instrumentation to all services
- [ ] Configure trace export (stdout/OTLP)
- [ ] Implement structured JSON logging
- [ ] Add service name and correlation ID to logs
- [ ] Add span attributes for case_id, evidence_id
- [ ] Implement readiness endpoints (`/ready`)
- [ ] Add database and Redis connectivity checks
- [ ] Test distributed tracing across services
- [ ] Add custom metrics for business events

## E2E Tests (happy path: upload → process → storyboard → timeline → render)

- [ ] Create E2E test framework (`tests/e2e/`)
- [ ] Implement happy path test (`test_happy_path.py`)
- [ ] Add Docker Compose integration for testing
- [ ] Create polling helper for async operations
- [ ] Test evidence upload → processing → storyboard creation
- [ ] Test storyboard → timeline compilation
- [ ] Test timeline → render orchestration
- [ ] Verify database state at each step
- [ ] Verify chain of custody and WORM locks
- [ ] Add make target for E2E tests (`make e2e`)

## Additional Integration Tasks

- [ ] API Gateway OpenAPI aggregation
- [ ] Python SDK generation (`scripts/gen-sdk.sh`)
- [ ] Feature flags implementation
- [ ] Request rate limiting
- [ ] Rollback procedures documentation
- [ ] Runbook creation (`docs/Runbook.md`)
- [ ] CI/CD pipeline integration
- [ ] Performance testing framework
- [ ] Security testing integration
- [ ] Documentation updates

## Completion Criteria

- [ ] All services communicate via HTTP with retries and circuit breakers
- [ ] Database operations work through repositories with proper sessions
- [ ] Event-driven workflow processes evidence end-to-end
- [ ] File storage implements WORM compliance with chain of custody
- [ ] Authorization policies enforce access control and mode restrictions
- [ ] Observability provides full traceability and health monitoring
- [ ] E2E tests validate complete happy path workflow
- [ ] All integration tests pass consistently
- [ ] Documentation is complete and up-to-date