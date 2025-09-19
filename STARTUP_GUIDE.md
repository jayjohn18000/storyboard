# Legal Simulation Platform - Startup Guide

## Quick Start

### 1. Start Backend Services

**Option A: Using the new startup script (Recommended)**
```bash
# From project root
python start_api_gateway.py
```

**Option B: Using make (if available)**
```bash
make dev
```

**Option C: Manual startup**
```bash
# Terminal 1: API Gateway
cd /Users/jaylenjohnson18/Storyboard
python start_api_gateway.py

# Terminal 2: Evidence Service
cd /Users/jaylenjohnson18/Storyboard/services/evidence_processor
python main.py

# Terminal 3: Database and other services
# Start PostgreSQL, Redis, MinIO, etc.
```

### 2. Start Frontend

```bash
cd web/case-dashboard
npm start
```

### 3. Verify Services

- **API Gateway**: http://localhost:8000/health
- **Evidence Service**: http://localhost:8001/health
- **Frontend**: http://localhost:3002

## Fixed Issues

### ✅ Python Import Path Issues
- **Problem**: `ModuleNotFoundError: No module named 'services'`
- **Solution**: 
  - Updated imports in `services/api_gateway/main.py` to use relative imports
  - Created `start_api_gateway.py` script that runs from project root with proper Python path

### ✅ TypeScript Compilation Errors
- **Problem**: Multiple TypeScript errors in frontend components
- **Solutions**:
  - Fixed arithmetic operation in `StoryboardFlowEditor.tsx` (added `Number()` cast)
  - Fixed date handling in `CaseOverview.tsx` (added `new Date()` constructor)
  - Fixed missing `caseId` prop in `CaseDetailPage.tsx`
  - Fixed `RenderJob` type compatibility in `RendersPage.tsx` (added proper type casting)

### ✅ Frontend-Backend Integration
- **Problem**: Frontend mocks not replaced with real API calls
- **Solution**: 
  - Updated all RTK Query services with proper data transformation
  - Replaced direct fetch calls with RTK Query mutations
  - Fixed data type mismatches between backend and frontend

## Testing the Integration

### 1. Test API Gateway
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/cases
```

### 2. Test Evidence Service
```bash
curl http://localhost:8001/health
curl http://localhost:8001/evidence
```

### 3. Test Frontend
- Navigate to http://localhost:3002
- Try uploading evidence files
- View case details and evidence lists
- Check that all data loads from real APIs

## Troubleshooting

### If API Gateway fails to start:
1. Make sure you're running from the project root
2. Use the `start_api_gateway.py` script
3. Check that all dependencies are installed: `pip install -r requirements.txt`

### If Frontend fails to compile:
1. Check that all TypeScript errors are resolved
2. Run `npm install` to ensure dependencies are up to date
3. Clear cache: `npm start -- --reset-cache`

### If services can't connect:
1. Verify all services are running on correct ports
2. Check firewall settings
3. Ensure database services (PostgreSQL, Redis) are running

## Next Steps

With these fixes, the platform should now:
- ✅ Start without import errors
- ✅ Compile without TypeScript errors  
- ✅ Connect frontend to backend APIs
- ✅ Handle evidence uploads with real processing
- ✅ Display real data from the database

The next priority items are:
1. Complete remaining backend TODOs
2. Fix StoryboardEditor React Flow integration
3. Test Temporal AI agent integration
