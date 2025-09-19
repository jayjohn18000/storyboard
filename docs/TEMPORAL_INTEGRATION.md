# Temporal Integration for AI Agents

This document describes the Temporal integration for AI agent orchestration in the Legal Simulation Platform.

## Overview

The Temporal integration provides:
- **Workflow Orchestration**: Manages AI agent workflows for evidence intake and timeline reconciliation
- **Event Bridge**: Connects Redis events to Temporal workflows
- **Worker Management**: Executes AI agent activities and workflows
- **Fault Tolerance**: Automatic retries and error handling
- **Scalability**: Horizontal scaling of AI agent processing

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Redis Events  │───▶│  Event Bridge   │───▶│ Temporal Server │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agents     │◀───│ Temporal Worker  │◀───│   Workflows     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. Temporal Workflows

**Location**: `services/shared/workflows/ai_agent_workflows.py`

- **EvidenceIntakeWorkflow**: Processes evidence uploads and categorization
- **TimelineReconciliationWorkflow**: Analyzes storyboard conflicts and suggests improvements
- **AIAgentOrchestrationWorkflow**: Orchestrates multiple AI agents for complex cases

### 2. Temporal Activities

Activities are the actual work units executed by AI agents:

- `process_evidence_intake`: Evidence categorization and triage
- `process_timeline_reconciliation`: Timeline conflict analysis
- `log_ai_processing_event`: Audit logging for AI processing
- `get_evidence_details`: Database queries for evidence
- `get_storyboard_details`: Database queries for storyboards
- `generate_ai_summary_report`: Summary report generation

### 3. Event Bridge

**Location**: `services/shared/events/temporal_event_bridge.py`

Listens to Redis events and triggers Temporal workflows:
- `evidence:uploaded` → EvidenceIntakeWorkflow
- `evidence:processed` → TimelineReconciliationWorkflow
- `storyboard:created` → TimelineReconciliationWorkflow
- `storyboard:updated` → TimelineReconciliationWorkflow

### 4. Temporal Worker

**Location**: `services/shared/workers/ai_agent_worker.py`

Executes workflows and activities:
- Registers workflows and activities
- Connects to Temporal server
- Processes tasks from the `ai-agent-queue`

## Configuration

### Environment Variables

```bash
# Temporal Server
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=legal-sim

# Redis
REDIS_URL=redis://localhost:6379

# Task Queue
AI_AGENT_TASK_QUEUE=ai-agent-queue
```

### Docker Compose

The Temporal integration is included in `docker-compose.yml`:

```yaml
services:
  temporal:
    image: temporalio/auto-setup:1.22.0
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=legal_sim
      - POSTGRES_PWD=password
      - POSTGRES_SEEDS=postgres
    ports:
      - "7233:7233"
    depends_on:
      postgres:
        condition: service_healthy

  temporal-worker:
    build:
      context: .
      dockerfile: infrastructure/docker/services/temporal-worker.Dockerfile
    environment:
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=legal-sim
      - AI_AGENT_TASK_QUEUE=ai-agent-queue
    depends_on:
      temporal:
        condition: service_started

  temporal-event-bridge:
    build:
      context: .
      dockerfile: infrastructure/docker/services/temporal-event-bridge.Dockerfile
    environment:
      - REDIS_URL=redis://redis:6379/0
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=legal-sim
    depends_on:
      temporal:
        condition: service_started
```

## Usage

### Starting Services

1. **Start Temporal Server**:
   ```bash
   docker-compose up temporal
   ```

2. **Start Temporal Worker**:
   ```bash
   docker-compose up temporal-worker
   ```

3. **Start Event Bridge**:
   ```bash
   docker-compose up temporal-event-bridge
   ```

### Manual Testing

Run the integration test:
```bash
python scripts/test_temporal_integration.py
```

### Starting Individual Components

1. **Temporal Worker**:
   ```bash
   python scripts/start_temporal_worker.py
   ```

2. **Event Bridge**:
   ```bash
   python scripts/start_temporal_event_bridge.py
   ```

3. **Temporal Server**:
   ```bash
   ./scripts/start_temporal_server.sh
   ```

## AI Agent Integration

### Evidence Intake Agent

**Location**: `agents/intake_triage/main.py`

- Automatically categorizes uploaded evidence
- Suggests relevant case associations
- Identifies duplicate uploads
- Extracts key information preview
- Routes to appropriate processors

**Temporal Integration**:
- Triggered by `evidence:uploaded` Redis event
- Executes `EvidenceIntakeWorkflow`
- Runs `process_evidence_intake` activity

### Timeline Reconciliation Agent

**Location**: `agents/timeline_reconciliation/main.py`

- Resolves temporal conflicts in storyboards
- Suggests missing events based on evidence
- Identifies logical inconsistencies
- Proposes alternative sequences
- Generates conflict reports

**Temporal Integration**:
- Triggered by `storyboard:created/updated` Redis events
- Executes `TimelineReconciliationWorkflow`
- Runs `process_timeline_reconciliation` activity

## Monitoring

### Temporal Web UI

Access the Temporal Web UI at: http://localhost:8080

- View workflow executions
- Monitor activity performance
- Debug workflow issues
- View task queue status

### Logs

All Temporal components log to stdout with structured logging:

```bash
# View worker logs
docker-compose logs -f temporal-worker

# View event bridge logs
docker-compose logs -f temporal-event-bridge

# View Temporal server logs
docker-compose logs -f temporal
```

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Ensure Temporal server is running
   - Check `TEMPORAL_HOST` environment variable
   - Verify network connectivity

2. **Workflow Not Found**:
   - Ensure worker is running and registered
   - Check workflow registration in worker
   - Verify namespace configuration

3. **Activity Timeout**:
   - Check activity implementation
   - Verify AI agent dependencies
   - Review timeout configurations

### Debug Commands

```bash
# Check Temporal server status
curl http://localhost:7233/api/v1/namespaces/legal-sim

# List workflows
temporal workflow list --namespace legal-sim

# View workflow execution
temporal workflow show --workflow-id <workflow-id> --namespace legal-sim
```

## Development

### Adding New Workflows

1. Define workflow in `services/shared/workflows/ai_agent_workflows.py`
2. Register workflow in `services/shared/workers/ai_agent_worker.py`
3. Add event trigger in `services/shared/events/temporal_event_bridge.py`
4. Test with `scripts/test_temporal_integration.py`

### Adding New Activities

1. Define activity function with `@workflow.activity` decorator
2. Register activity in worker
3. Call activity from workflow
4. Test activity execution

### Adding New AI Agents

1. Implement agent in `agents/<agent-name>/main.py`
2. Create Temporal activity wrapper
3. Add workflow for agent orchestration
4. Update event bridge for triggers

## Security

- All AI agents operate in **Sandbox mode only**
- Workflows enforce case mode validation
- Audit logging for all AI processing events
- Temporal server runs in isolated Docker container

## Performance

- Workflows support parallel execution
- Activities can be scaled horizontally
- Retry policies for fault tolerance
- Configurable timeouts and limits

## Future Enhancements

- [ ] Add more AI agents (scene drafting, evidence analysis)
- [ ] Implement workflow versioning
- [ ] Add metrics and monitoring
- [ ] Implement workflow scheduling
- [ ] Add workflow templates
