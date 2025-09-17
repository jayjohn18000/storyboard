# Legal Simulation Platform - Auto-Discovery Inventory

## Stack Detection

**Frontend**: Create React App (not Next.js App Router)
- **Path**: `/web/case-dashboard/`
- **Framework**: React 18.2.0 + TypeScript 4.9.5
- **State Management**: Redux Toolkit + RTK Query
- **Routing**: React Router DOM v6
- **Styling**: Tailwind CSS 3.3.5
- **UI Components**: Heroicons, React Dropzone, Monaco Editor, React Flow
- **Port**: 3002 (configured in package.json)

**Backend**: FastAPI + Python
- **API Gateway**: `/services/api_gateway/` (port 8000)
- **Services**: Evidence Processor, Storyboard Service, Timeline Compiler, Render Orchestrator
- **Database**: PostgreSQL with Alembic migrations
- **Storage**: MinIO/S3 support
- **Auth**: JWT middleware (disabled in dev)

## Key Components & Pages

### Frontend Components
- **EvidenceUploader**: `/web/case-dashboard/src/shared/components/evidence/EvidenceUploader.tsx` ✅ (with SHA-256, progress UI)
- **StoryboardEditor**: `/web/case-dashboard/src/shared/components/storyboard/StoryboardEditor.tsx` ✅ (Monaco Editor, StoryDoc syntax)
- **TimelineEditor**: `/web/case-dashboard/src/shared/components/timeline/TimelineEditor.tsx` (not found)
- **RenderProgressMonitor**: `/web/case-dashboard/src/shared/components/render/RenderProgressMonitor.tsx` (not found)

### Pages
- **CasesPage**: `/web/case-dashboard/src/pages/cases/CasesPage.tsx`
- **CaseDetailPage**: `/web/case-dashboard/src/pages/cases/CaseDetailPage.tsx`
- **EvidencePage**: `/web/case-dashboard/src/pages/evidence/EvidencePage.tsx`
- **StoryboardPage**: `/web/case-dashboard/src/pages/storyboard/StoryboardPage.tsx`
- **RendersPage**: `/web/case-dashboard/src/pages/renders/RendersPage.tsx`
- **CaseOverview**: `/web/case-dashboard/src/pages/CaseOverview.tsx` ✅ (comprehensive dashboard)

## Mock Data Locations

### Frontend Mocks
- **Cases API**: `/web/case-dashboard/src/store/api/casesApi.ts` (lines 55-87, 92-107) - hardcoded mock data
- **CaseOverview**: `/web/case-dashboard/src/pages/CaseOverview.tsx` (lines 76-142) - setTimeout simulation
- **EvidenceUploader**: `/web/case-dashboard/src/shared/components/evidence/EvidenceUploader.tsx` (lines 105-115) - simulateUpload function

### Backend TODOs
- **Cases Router**: `/services/api_gateway/routers/cases.py` - lines 143-153, 186-198, 216-231, 248-263, 280-284, 301-305, 322-326
- **Evidence Router**: `/services/api_gateway/routers/evidence.py` - lines 110-125, 343-368, 385-407, 522-537, 554-568
- **Storyboards Router**: `/services/api_gateway/routers/storyboards.py` - lines 131-132, 164-189, 206-218, 236-254, 272-286, 304-318, 336-392, 409-424

## API Layer Status

### RTK Query Services
- **baseApi**: `/web/case-dashboard/src/store/api/baseApi.ts` ✅ (auth headers, base URL)
- **casesApi**: `/web/case-dashboard/src/store/api/casesApi.ts` ✅ (with mocks)
- **evidenceApi**: `/web/case-dashboard/src/store/api/evidenceApi.ts` (not examined)
- **storyboardsApi**: `/web/case-dashboard/src/store/api/storyboardsApi.ts` (not examined)
- **rendersApi**: `/web/case-dashboard/src/store/api/rendersApi.ts` (not examined)

### Auth Middleware
- **ProtectedRoute**: `/web/case-dashboard/src/components/auth/ProtectedRoute.tsx` ✅
- **Auth Utils**: `/web/case-dashboard/src/utils/auth.ts` ✅
- **Backend Auth**: `/services/api_gateway/middleware/auth.py` ✅ (JWT disabled in dev)

## Backend Endpoints Status

### Cases API (`/api/v1/cases`)
- ✅ POST `/` - Create case (implemented)
- ❌ GET `/` - List cases (TODO: lines 143-153)
- ❌ GET `/{case_id}` - Get case (TODO: lines 186-198)
- ❌ PUT `/{case_id}` - Update case (TODO: lines 216-231)
- ❌ DELETE `/{case_id}` - Delete case (TODO: lines 248-263)
- ❌ GET `/{case_id}/evidence` - Get case evidence (TODO: lines 280-284)
- ❌ GET `/{case_id}/storyboards` - Get case storyboards (TODO: lines 301-305)
- ❌ GET `/{case_id}/renders` - Get case renders (TODO: lines 322-326)

### Evidence API (`/api/v1/evidence`)
- ❌ POST `/upload` - Upload evidence (TODO: lines 110-125)
- ✅ GET `/` - List evidence (implemented with service proxy)
- ✅ GET `/{evidence_id}` - Get evidence (implemented with service proxy)
- ❌ PUT `/{evidence_id}` - Update evidence (TODO: lines 343-368)
- ❌ DELETE `/{evidence_id}` - Delete evidence (TODO: lines 385-407)
- ✅ POST `/{evidence_id}/commit` - Commit evidence (implemented)
- ❌ GET `/{evidence_id}/download` - Download evidence (TODO: lines 522-537)

### Storyboards API (`/api/v1/storyboards`)
- ❌ POST `/` - Create storyboard (TODO: lines 131-132)
- ❌ GET `/` - List storyboards (TODO: lines 164-189)
- ❌ GET `/{storyboard_id}` - Get storyboard (TODO: lines 206-218)
- ❌ PUT `/{storyboard_id}` - Update storyboard (TODO: lines 236-254)
- ❌ DELETE `/{storyboard_id}` - Delete storyboard (TODO: lines 272-286)
- ❌ POST `/{storyboard_id}/validate` - Validate storyboard (TODO: lines 304-318)
- ✅ POST `/{storyboard_id}/compile` - Compile storyboard (implemented with service proxy)
- ❌ GET `/{storyboard_id}/evidence-coverage` - Get evidence coverage (TODO: lines 409-424)

## Temporal Setup

### Configuration
- **Host**: localhost:7233 ✅
- **Namespace**: legal-sim ✅
- **Config**: `/temporal/config/dynamicconfig/development.yaml` ✅

### AI Agents
- **Intake Triage Agent**: `/agents/intake-triage/main.py` ✅ (comprehensive ML pipeline)
- **Timeline Reconciliation Agent**: `/agents/timeline-reconciliation/main.py` ✅ (conflict detection)

### Missing Temporal Integration
- ❌ No Temporal workflows defined
- ❌ No Temporal activities for AI agents
- ❌ No Temporal workers
- ❌ No event bridge (Redis → Temporal)

## Database & Migrations

### Alembic Setup
- **Config**: `/alembic.ini` ✅
- **Env**: `/alembic/env.py` ✅
- **Initial Migration**: `/alembic/versions/0001_init.py` ✅ (comprehensive schema)
- **Chain of Custody**: `/alembic/versions/0002_chain_of_custody.py` ✅

### Schema Status
- ✅ Users table with roles
- ✅ Cases table with metadata
- ✅ Evidence table with processing results
- ✅ Storyboards table with scenes JSON
- ✅ Renders table with status tracking
- ✅ Audit logs table
- ✅ Export jobs table

## Environment Configuration

### Backend (.env.example)
- ✅ API Gateway: localhost:8000
- ✅ Service URLs configured
- ✅ Database: PostgreSQL
- ✅ Redis: localhost:6379
- ✅ Storage: MinIO localhost:9000
- ✅ Temporal: localhost:7233
- ✅ JWT secret configured

### Frontend Environment
- ❌ No `.env` file found
- ✅ API URL: `process.env.REACT_APP_API_URL || 'http://localhost:8000'`
- ✅ Mock toggle: Not implemented

## Gaps Identified

### Critical Gaps
1. **Frontend Environment**: No `.env` file, no mock toggle
2. **Backend TODOs**: Most CRUD endpoints return 404/mock responses
3. **Temporal Integration**: No workflows/activities for AI agents
4. **Storage Integration**: Upload endpoints not implemented
5. **Auth**: JWT middleware disabled in development

### Missing Components
1. **TimelineEditor**: Referenced but not found
2. **RenderProgressMonitor**: Referenced but not found
3. **Docs Dashboard**: No dedicated docs page
4. **Query Interface**: No document-augmented query UI

### Service Integration
1. **Evidence Service**: Proxy calls implemented but service may not be running
2. **Storyboard Service**: Compile endpoint proxied but service may not be running
3. **Storage Service**: MinIO/S3 integration not implemented
4. **AI Agent Orchestration**: No Temporal workflows

## Next Steps Priority

1. **Ticket 1**: Replace frontend mocks with real API calls
2. **Ticket 6**: Implement backend TODOs with real DB queries
3. **Ticket 4**: Create Temporal workflows for AI agents
4. **Ticket 2**: Implement evidence upload with storage integration
5. **Ticket 3**: Fix StoryboardEditor (React Flow integration)

## Files Changed in Auto-Discovery
- Created: `AUTO_DISCOVERY_INVENTORY.md`

## Manual Test Steps
1. Start backend services: `make dev` or individual service startup
2. Start frontend: `cd web/case-dashboard && npm start`
3. Verify API Gateway health: `curl http://localhost:8000/health`
4. Check database connection and migrations
5. Verify Temporal server: `curl http://localhost:7233/api/v1/namespaces/legal-sim`

## Follow-ups
- Create `.env` file for frontend
- Implement mock toggle environment variable
- Set up service health checks
- Create Temporal workflow definitions
- Implement storage service integration
