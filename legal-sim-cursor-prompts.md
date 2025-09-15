# Legal-Sim Cursor Development Prompts

## Overview
This document contains sequential prompts for building Legal-Sim using Cursor. Each prompt builds on the previous one. Complete each section fully before moving to the next.

**Note**: Phases 1-5 are already completed! The project has a solid foundation with:
- ✅ Complete microservices architecture
- ✅ All service interfaces and data models
- ✅ Evidence processing pipeline (OCR, ASR, NLP)
- ✅ Storyboard parsing and validation system
- ✅ Timeline compilation with OpenTimelineIO
- ✅ Policy engine and RBAC

---

## ✅ COMPLETED PHASES (Skip These)

### Phase 1: Project Foundation - COMPLETE
- ✅ Monorepo structure with services/, config/, infrastructure/
- ✅ Docker-compose.yml with PostgreSQL, MinIO, Redis, OPA, Cerbos
- ✅ pyproject.toml with dependencies
- ✅ Database schema and environment configuration

### Phase 2: Service Interfaces & Models - COMPLETE
- ✅ All abstract service interfaces (storage, OCR, ASR, renderer, policy)
- ✅ Complete data models with SQLAlchemy relationships

### Phase 3: Factory Pattern & MVP Implementations - COMPLETE
- ✅ Service factories for all major services
- ✅ Multiple storage implementations (MinIO, S3, Local)
- ✅ Multiple OCR implementations (Tesseract, PaddleOCR, OCRMyPDF)
- ✅ Multiple ASR implementations (WhisperX, PyAnnote)

### Phase 4: Evidence Processing Pipeline - COMPLETE
- ✅ OCR service implementations
- ✅ ASR service implementations with diarization
- ✅ Evidence processing pipelines

### Phase 5: Storyboard & Timeline System - COMPLETE
- ✅ Storyboard parsers (bullet, storydoc, jsonl)
- ✅ Validators (anchor, coverage, lint engine)
- ✅ Timeline compilation with OpenTimelineIO
- ✅ Scene graph components (USD builder, spatial solver, trajectory generator)

---

## Phase 6: Rendering Pipeline (COMPLETE)

**Status**: ✅ Blender integration and video post-processing implemented

### Prompt 6.1: Blender Integration for Rendering
```
In services/render-orchestrator/implementations/blender/, create the deterministic rendering system.

Create:

1. local_renderer.py:
   - Implements RenderService using Blender Python API
   - Executes Blender in headless mode
   - Loads USD scenes into Blender
   - Applies render profiles (neutral vs cinematic)
   - Manages deterministic seeds for all random operations
   - Outputs frame sequences or video files

2. profiles/neutral.py:
   - Defines court-appropriate render settings
   - Flat lighting (no dramatic shadows)
   - Neutral colors and materials
   - Fixed camera angles (no dramatic movements)
   - Consistent environment lighting
   - Disabled motion blur and depth of field

3. profiles/cinematic.py:
   - Sandbox mode only settings
   - Dynamic lighting and shadows
   - Camera movements and transitions
   - Enhanced materials and textures
   - Atmospheric effects allowed

4. determinism.py:
   - Manages random seeds for all operations
   - Locks Blender's random number generators
   - Ensures frame-perfect reproducibility
   - Implements checksum verification
   - Creates determinism test suite

Include render progress reporting, frame caching, and error recovery.
```

**Validation Check**: Render same scene 3 times with same seed, verify SHA-256 of output videos match.

### Prompt 6.2: Video Post-Processing Pipeline
```
In services/render-orchestrator/implementations/overlays/, create video post-processing system.

Create:

1. ffmpeg_processor.py:
   - Adds text overlays using FFmpeg drawtext
   - Burns in evidence citations at specific timestamps  
   - Adds watermarks based on mode (SANDBOX/DEMONSTRATIVE)
   - Implements picture-in-picture for evidence display
   - Handles multiple overlay tracks

2. citation_burner.py:
   - Formats legal citations according to jurisdiction rules
   - Places citations near relevant scene elements
   - Implements smart positioning to avoid occlusion
   - Fades citations in/out smoothly
   - Tracks citation display duration for compliance

3. uncertainty_overlay.py:
   - Visualizes confidence levels for disputed facts
   - Adds uncertainty indicators (dotted outlines, transparency)
   - Implements "alleged" labels for disputed elements
   - Shows confidence percentages when required
   - Creates visual distinction for facts vs interpretations

4. evidence_overlay.py:
   - Embeds actual evidence (photos, documents) as overlays
   - Implements Ken Burns effect for document display
   - Synchronizes evidence display with timeline
   - Handles multiple evidence items simultaneously

Include render queue management and GPU acceleration support.
```

**Validation Check**: Process a video with 10 different citation overlays and verify all are readable and correctly timed.

---

## Phase 7: Policy Engine & Validation (COMPLETE)

**Status**: ✅ OPA policies and RBAC already implemented

### Phase 7: Policy Engine & Validation - COMPLETE
- ✅ OPA policy implementation (opa-policies.rego)
- ✅ RBAC policies (Cerbos configuration)
- ✅ Policy validation system

---

## Phase 8: Frontend Applications (COMPLETE)

**Status**: ✅ React component library and dashboard applications implemented

### Prompt 8.1: React Component Library
```
In web/shared/components/, create reusable React components for the legal visualization system.

Create:

1. evidence/EvidenceUploader.tsx:
   - Drag-and-drop file upload with progress
   - Real-time SHA-256 calculation in browser
   - File type validation and preview
   - Metadata entry form
   - Chain of custody tracking UI

2. timeline/TimelineEditor.tsx:
   - Visual timeline using React Flow
   - Drag-and-drop beat arrangement
   - Evidence anchor management
   - Confidence level sliders
   - Dispute flagging interface

3. storyboard/StoryboardEditor.tsx:
   - Rich text editor for narrative entry
   - Auto-linking of evidence references
   - Syntax highlighting for StoryDoc format
   - Real-time validation feedback
   - Side-by-side preview

4. render/RenderProgressMonitor.tsx:
   - Real-time render progress display
   - Frame preview thumbnails
   - Resource usage graphs
   - Error display and recovery options
   - Queue position indicator

Use TypeScript, Tailwind CSS, and implement accessibility standards (WCAG 2.1 AA).
```

**Validation Check**: Run Storybook and verify all components render correctly with mock data.

### Prompt 8.2: Main Dashboard Application
```
In web/case-dashboard/, create the main React application.

Create:

1. src/pages/CaseOverview.tsx:
   - Display case metadata and status
   - Show evidence summary with thumbnails
   - Timeline visualization preview
   - Validation status indicators
   - Quick action buttons

2. src/pages/EvidenceManager.tsx:
   - Evidence grid/list view with filtering
   - Detailed evidence viewer
   - OCR/ASR result display
   - Evidence relationship graph
   - Batch operations support

3. src/pages/StoryboardWorkspace.tsx:
   - Integrated editor with live preview
   - Evidence picker sidebar
   - Beat timeline visualization
   - Coverage meter display
   - Collaboration features (comments, suggestions)

4. src/pages/RenderStudio.tsx:
   - Render configuration interface
   - Profile selection (neutral/cinematic)
   - Seed management for determinism
   - Preview player with annotation tools
   - Export options and format selection

Implement proper state management with Redux Toolkit, API integration with RTK Query, and comprehensive error handling.
```

**Validation Check**: Create a full case workflow from upload to render and verify smooth user experience.

---

## Phase 9: Testing & Quality Assurance (PARTIALLY COMPLETE)

**Status**: ✅ Basic test setup exists, ❌ Comprehensive test suite needed

### Prompt 9.1: Comprehensive Test Suite
```
In tests/, create a comprehensive testing framework covering all aspects of the system.

Create:

1. integration/test_evidence_pipeline.py:
   - Test complete evidence processing flow
   - Verify OCR accuracy on legal documents
   - Test ASR with legal audio samples
   - Validate NLP extraction accuracy
   - Check storage integrity and WORM compliance

2. determinism/test_render_determinism.py:
   - Create golden test cases
   - Test render reproducibility across runs
   - Verify seed propagation through pipeline
   - Test with various scene complexities
   - Validate checksum consistency

3. compliance/test_policy_compliance.py:
   - Test each jurisdiction's rules
   - Verify validation catches violations
   - Test edge cases and boundaries
   - Validate remediation suggestions
   - Check policy versioning

4. performance/test_load_scenarios.py:
   - Simulate concurrent case processing
   - Test with large evidence files (1GB+)
   - Measure render queue performance
   - Test database query optimization
   - Profile memory usage

Include fixtures for test data, mocks for external services, and comprehensive assertions.
```

**Validation Check**: Run full test suite with coverage report, ensure >90% coverage.

### Prompt 9.2: End-to-End Test Scenarios
```
In tests/e2e/, create Playwright tests for complete user workflows.

Create:

1. test_case_creation_flow.py:
   - Test case creation with all metadata
   - Upload multiple evidence types
   - Create storyboard from template
   - Generate timeline
   - Render preview

2. test_demonstrative_workflow.py:
   - Create demonstrative case
   - Process evidence with high accuracy
   - Build fully anchored storyboard
   - Pass all validation checks
   - Generate signed export

3. test_collaboration_features.py:
   - Multi-user case access
   - Comment and review workflow
   - Approval chain testing
   - Permission enforcement
   - Audit trail verification

4. test_error_recovery.py:
   - Test upload failures and retry
   - Render crash recovery
   - Network interruption handling
   - Partial state recovery
   - Data integrity after errors

Include visual regression tests for rendered outputs.
```

**Validation Check**: Run E2E tests in CI pipeline, all should pass in under 30 minutes.

---

## Phase 10: DevOps & Deployment (PARTIALLY COMPLETE)

**Status**: ✅ Docker orchestration exists, ❌ Kubernetes and CI/CD needed

### Prompt 10.1: Container Orchestration
```
In infrastructure/kubernetes/, create production-ready Kubernetes configurations.

Create:

1. base/deployments/:
   - Deployment configs for each service
   - Resource limits and requests
   - Health checks and readiness probes
   - Environment-specific configs
   - Sidecar containers for logging

2. base/services/:
   - Service definitions with proper ports
   - Load balancer configurations  
   - Internal service mesh setup
   - Ingress rules for external access

3. base/jobs/:
   - CronJob for cleanup tasks
   - Job templates for batch processing
   - Render worker job definitions
   - Database migration jobs

4. overlays/production/:
   - Production-specific resources
   - Horizontal pod autoscaling
   - Pod disruption budgets
   - Network policies
   - Secret management with Sealed Secrets

Include monitoring with Prometheus ServiceMonitors and Grafana dashboards.
```

**Validation Check**: Deploy to local Kubernetes (kind/minikube) and verify all pods healthy.

### Prompt 10.2: CI/CD Pipeline
```
In .github/workflows/, create comprehensive CI/CD pipelines.

Create:

1. ci.yml:
   - Run on all pull requests
   - Execute unit tests with coverage
   - Run integration tests
   - Perform static analysis (mypy, ruff, ESLint)
   - Check license compliance
   - Build and scan Docker images
   - Generate test reports

2. determinism-check.yml:
   - Nightly determinism verification
   - Run golden test cases
   - Compare render outputs
   - Alert on determinism failures
   - Generate reproducibility report

3. deploy-staging.yml:
   - Deploy to staging on main branch
   - Run smoke tests
   - Execute performance tests
   - Validate all services healthy
   - Run E2E test suite

4. deploy-production.yml:
   - Manual approval required
   - Blue-green deployment
   - Database migration execution
   - Health check validation
   - Rollback on failure

Include secret scanning, dependency updates, and security alerts.
```

**Validation Check**: Make a test PR and verify all CI checks pass.

---

## Phase 11: Production Hardening (NOT STARTED)

**Status**: ❌ Security and operational tools needed

### Prompt 11.1: Security Implementation
```
Implement comprehensive security measures across the system.

Create:

1. services/shared/security/encryption.py:
   - Implement envelope encryption for evidence
   - Use AES-256 for data at rest
   - Implement key rotation
   - Add field-level encryption for PII
   - Create encryption audit trail

2. services/shared/security/authentication.py:
   - Implement JWT-based authentication
   - Add refresh token mechanism
   - Support MFA/2FA
   - Implement session management
   - Add brute force protection

3. services/shared/security/audit.py:
   - Create tamper-proof audit logging
   - Implement log shipping to SIEM
   - Add suspicious activity detection
   - Create compliance reports
   - Implement legal hold functionality

4. infrastructure/security/:
   - Network segmentation configs
   - WAF rules for API gateway
   - Certificate management
   - Secret rotation automation
   - Intrusion detection setup

Include penetration testing scenarios and security scanning automation.
```

**Validation Check**: Run security scan with OWASP ZAP and fix any high/critical findings.

### Prompt 11.2: Operational Excellence
```
Implement production monitoring, alerting, and operational tools.

Create:

1. monitoring/dashboards/:
   - System health dashboard
   - Business metrics dashboard
   - Render queue performance
   - Storage usage trends
   - User activity analytics

2. monitoring/alerts/:
   - SLO-based alerting rules
   - Determinism failure alerts
   - Security incident alerts
   - Resource threshold alerts
   - Business metric alerts

3. tools/cli/commands/:
   - Case debugging commands
   - Evidence verification tools
   - Render troubleshooting
   - System health checks
   - Backup verification

4. scripts/operations/:
   - Automated backup scripts
   - Disaster recovery procedures
   - Data migration tools
   - Performance tuning scripts
   - Capacity planning tools

Include runbooks for common operational scenarios.
```

**Validation Check**: Simulate system failure and verify recovery within RTO/RPO targets.

---

## Phase 12: Advanced Features (NOT STARTED)

**Status**: ❌ AI agents and advanced visualization needed

### Prompt 12.1: AI Agent Implementation
```
In agents/, implement autonomous agents for Sandbox mode only.

Create:

1. intake-triage/main.py:
   - Automatically categorize uploaded evidence
   - Suggest relevant case associations
   - Identify duplicate uploads
   - Extract key information preview
   - Route to appropriate processors

2. timeline-reconciliation/main.py:
   - Resolve temporal conflicts in storyboards
   - Suggest missing events based on evidence
   - Identify logical inconsistencies
   - Propose alternative sequences
   - Generate conflict reports

3. scene-drafting/main.py:
   - Generate initial scene layouts from descriptions
   - Suggest camera angles for clarity
   - Place actors based on testimony
   - Create movement paths
   - Optimize for visibility

4. shared/guardrails.py:
   - Enforce Sandbox-only operation
   - Prevent modification of approved data
   - Log all agent actions
   - Implement confidence thresholds
   - Add human-in-the-loop confirmations

Ensure all agents are optional and can be disabled.
```

**Validation Check**: Run agents on test cases and verify suggestions are reasonable and safe.

### Prompt 12.2: Advanced Visualization Features
```
Implement advanced visualization capabilities for complex cases.

Create:

1. services/visualization/heatmap_generator.py:
   - Generate evidence coverage heatmaps
   - Create confidence visualization overlays
   - Show temporal density maps
   - Visualize actor movement patterns
   - Generate dispute area highlighting

2. services/visualization/relationship_grapher.py:
   - Create entity relationship diagrams
   - Show evidence connection graphs
   - Visualize timeline dependencies
   - Generate actor interaction networks
   - Create citation networks

3. web/components/advanced/MultiAngleViewer.tsx:
   - Synchronized multi-angle playback
   - Split-screen comparison views
   - Frame-by-frame analysis tools
   - Annotation and markup features
   - Export for presentation

4. web/components/advanced/EvidenceExplorer.tsx:
   - 3D evidence relationship visualization
   - Interactive timeline scrubbing
   - Evidence clustering by similarity
   - Smart search with NLP
   - Bulk analysis tools

Include VR/AR preview capabilities for future expansion.
```

**Validation Check**: Create complex visualization with 100+ evidence items and verify performance.

---

## Final Integration & Launch Preparation

### Prompt 13: System Integration & Launch Readiness
```
Perform final integration testing and prepare for production launch.

Create:

1. scripts/launch/preflight_check.py:
   - Verify all services are healthy
   - Check database migrations are current
   - Validate all configurations
   - Test external service connections
   - Verify backup systems
   - Check monitoring is active
   - Validate security settings

2. docs/launch/checklist.md:
   - Technical readiness checklist
   - Legal compliance verification
   - User training materials
   - Support documentation
   - Incident response procedures
   - Rollback plans
   - Communication templates

3. tests/acceptance/full_system_test.py:
   - Complete workflow from case creation to export
   - Multi-user collaboration test
   - Jurisdiction-specific validation
   - Performance under load
   - Disaster recovery validation
   - Security penetration test
   - Compliance audit

Run complete system for 48 hours under load without issues before launch.
```

**Final Validation**: Execute launch readiness checklist and verify all items pass.

---

## Success Criteria

Before considering the system complete, verify:

1. ✅ All tests pass with >90% coverage
2. ✅ Deterministic rendering works 99.99% of the time
3. ✅ System handles 100 concurrent users
4. ✅ Evidence processing <5 minutes for typical documents
5. ✅ Render time <60 minutes for 5-minute videos
6. ✅ All jurisdiction policies implemented and tested
7. ✅ Security scan shows no high/critical vulnerabilities
8. ✅ Documentation complete for all user roles
9. ✅ Monitoring alerts configured and tested
10. ✅ Disaster recovery tested and documented

## Notes for Cursor Development

- Use Cursor's multi-file editing for related changes
- Leverage Cursor's test generation for comprehensive coverage
- Use Cursor's refactoring tools to maintain clean code
- Enable Cursor's type checking for Python and TypeScript
- Use Cursor's documentation generation features
- Leverage Cursor chat for implementation questions
- Use .cursorrules to maintain coding standards

Remember: Build incrementally, test thoroughly, and maintain clean architecture throughout!