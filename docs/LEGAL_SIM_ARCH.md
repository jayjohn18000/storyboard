# Legal Simulation Platform - Technical Architecture Overview

## System Overview

The Legal Simulation Platform is a microservices-based system designed to process legal evidence, create interactive storyboards, compile timelines, and generate courtroom visualizations. The platform follows a domain-driven design approach with clear service boundaries and event-driven communication.

## Core Services

### 1. API Gateway (`api-gateway`)
- **Purpose**: Single entry point for all client requests
- **Responsibilities**: 
  - Request routing and load balancing
  - Authentication and authorization
  - Rate limiting and circuit breaking
  - API aggregation and documentation
- **Port**: 8000
- **Technology**: FastAPI with middleware stack

### 2. Evidence Processor (`evidence-processor`)
- **Purpose**: Process uploaded evidence files (documents, audio, video)
- **Responsibilities**:
  - File ingestion and validation
  - OCR for documents
  - ASR (Automatic Speech Recognition) for audio
  - Content extraction and indexing
  - Chain of custody tracking
- **Port**: 8001
- **Technology**: FastAPI with specialized processing pipelines

### 3. Storyboard Service (`storyboard-service`)
- **Purpose**: Create and manage interactive storyboards from evidence
- **Responsibilities**:
  - Narrative construction from evidence
  - Scene organization and sequencing
  - Interactive element management
  - Version control and collaboration
- **Port**: 8002
- **Technology**: FastAPI with narrative processing engines

### 4. Timeline Compiler (`timeline-compiler`)
- **Purpose**: Compile storyboards into precise timelines
- **Responsibilities**:
  - Temporal sequence optimization
  - OTIO (Open Timeline IO) integration
  - Scene graph construction
  - Timeline validation and export
- **Port**: 8003
- **Technology**: FastAPI with OTIO processing

### 5. Render Orchestrator (`render-orchestrator`)
- **Purpose**: Generate final courtroom visualizations
- **Responsibilities**:
  - Blender integration for 3D rendering
  - Overlay and annotation management
  - Render job orchestration
  - Output format generation
- **Port**: 8004
- **Technology**: FastAPI with Blender integration

## Data Flow Architecture

```
Client → API Gateway → [Evidence Processor → Storyboard Service → Timeline Compiler → Render Orchestrator]
                    ↓
                Event Bus (Redis)
                    ↓
              [Processing Agents]
```

## Key Architectural Patterns

### 1. Event-Driven Architecture
- **Event Bus**: Redis pub/sub for asynchronous communication
- **Event Types**: EvidenceUploaded, EvidenceProcessed, StoryboardCreated, TimelineCompiled, RenderCompleted
- **Benefits**: Decoupling, scalability, fault tolerance

### 2. Domain-Driven Design
- **Bounded Contexts**: Each service owns its domain model
- **Repository Pattern**: Data access abstraction
- **Service Interfaces**: Clear contracts between services

### 3. Chain of Custody
- **WORM Storage**: Write-Once, Read-Many for evidence integrity
- **Audit Trail**: Complete action logging
- **Immutable Records**: Evidence locking after commit

### 4. Policy-Driven Security
- **RBAC**: Role-based access control
- **OPA Integration**: Open Policy Agent for complex policies
- **Mode Enforcement**: Sandbox vs Demonstrative modes

## Technology Stack

### Backend Services
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Event Bus**: Redis
- **HTTP Client**: httpx with retry/circuit breaker

### Processing Engines
- **OCR**: Tesseract, Google Vision API
- **ASR**: Whisper, Google Speech-to-Text
- **Rendering**: Blender Python API
- **Timeline**: Open Timeline IO (OTIO)

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Monitoring**: OpenTelemetry, Prometheus, Grafana
- **Storage**: Local filesystem (dev), S3-compatible (prod)

## Security Model

### Authentication
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: Attorney, Judge, Clerk, Admin roles
- **Session Management**: Secure token handling

### Authorization
- **Policy Engine**: OPA/Cerbos integration
- **Resource-Based**: Fine-grained permissions
- **Mode Enforcement**: Sandbox restrictions

### Data Protection
- **Encryption**: TLS in transit, AES at rest
- **Chain of Custody**: Immutable audit trail
- **WORM Compliance**: Write-once evidence storage

## Deployment Architecture

### Development Environment
- **Local Development**: Docker Compose with hot reload
- **Service Discovery**: Environment-based URL configuration
- **Database**: Single PostgreSQL instance
- **Storage**: Local filesystem

### Production Environment
- **Kubernetes**: Container orchestration
- **Service Mesh**: Istio for traffic management
- **Database**: PostgreSQL cluster with replication
- **Storage**: Distributed object storage (S3-compatible)
- **Monitoring**: Full observability stack

## Integration Points

### External Systems
- **Court Management Systems**: REST API integration
- **Document Management**: SharePoint, Box integration
- **Video Conferencing**: Zoom, Teams integration
- **Case Law Databases**: Legal research APIs

### Internal Agents
- **Intake-Triage Agent**: Automated case assessment
- **Timeline Reconciliation Agent**: Conflict resolution
- **Quality Assurance Agent**: Output validation

## Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: Easy horizontal scaling
- **Load Balancing**: Round-robin with health checks
- **Database Sharding**: By case/tenant
- **Event Partitioning**: Topic-based partitioning

### Performance Optimization
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery
- **Async Processing**: Background job queues
- **Resource Pooling**: Connection pooling

## Monitoring and Observability

### Metrics
- **Service Health**: Uptime, response times, error rates
- **Business Metrics**: Cases processed, render completion rates
- **Resource Usage**: CPU, memory, disk, network
- **Custom Metrics**: Evidence processing time, render quality

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Aggregation**: Centralized log collection
- **Log Retention**: Configurable retention policies
- **Audit Logging**: Security and compliance events

### Tracing
- **Distributed Tracing**: OpenTelemetry integration
- **Span Correlation**: Cross-service request tracking
- **Performance Analysis**: Latency and bottleneck identification
- **Error Tracking**: Exception and failure analysis

## Compliance and Governance

### Legal Compliance
- **Chain of Custody**: Complete audit trail
- **Data Retention**: Configurable retention policies
- **Privacy**: GDPR/CCPA compliance
- **Security**: SOC 2, ISO 27001 alignment

### Operational Governance
- **Change Management**: GitOps workflow
- **Release Management**: Blue-green deployments
- **Incident Response**: Runbook and escalation procedures
- **Disaster Recovery**: Backup and restore procedures