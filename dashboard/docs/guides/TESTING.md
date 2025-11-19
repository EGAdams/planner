# Testing Guide - Pydantic Server Startup

## Quick Start

```bash
# Run all backend tests
npm test

# Run specific E2E test
npx playwright test tests/pydantic-server-startup.spec.ts

# Run with UI
npx playwright test tests/pydantic-server-startup.spec.ts --ui
```

## Test Structure

```
dashboard/
├── backend/
│   └── __tests__/
│       ├── processManager.test.ts       # ✓ Process lifecycle (7 tests)
│       ├── processMonitor.test.ts       # ✓ Health monitoring (7 tests)
│       ├── processStateStore.test.ts    # ✓ State persistence (5 tests)
│       ├── serverOrchestrator.test.ts   # ✓ Server coordination (25 tests)
│       └── server.test.ts               # ✗ HTTP endpoints (7 tests - need live server)
│
├── tests/
│   ├── managed-servers.spec.ts          # ✓ Existing UI tests (needs port fix)
│   └── pydantic-server-startup.spec.ts  # ✗ New Pydantic tests (12 tests)
│
└── playwright.config.ts                  # Playwright configuration
```

## Test Categories

### Unit Tests (Jest)
Tests individual components and services in isolation.

**Status**: 44/51 passing (86%)

```bash
npm test
```

### Integration Tests (Jest)
Tests requiring live server connections.

**Status**: Separate suite needed (currently mixed with unit tests)

### E2E Tests (Playwright)
Tests complete user workflows in real browsers.

**Status**: 2/12 passing (17% - expected, server won't start)

```bash
npx playwright test
```

## Current Issues

1. **UV Command Missing**: Server can't start without `uv` binary
2. **Port Mismatch**: Old test checks port 8000, should be 8001
3. **Missing .env**: Supabase credentials not configured

## Fix Required

See `/home/adamsl/planner/dashboard/IMPLEMENTATION_FIXES.md` for detailed instructions.

Quick fix:
```bash
# 1. Update server.ts line 53
sed -i "s|uv run python|/home/adamsl/planner/venv/bin/python|" backend/server.ts

# 2. Rebuild
npm run build:backend

# 3. Create .env (add your credentials)
cat > /home/adamsl/planner/.env << 'ENVEOF'
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-key
API_BEARER_TOKEN=your-token
ADMIN_PORT=3030
ADMIN_HOST=127.0.0.1
ENVEOF

# 4. Re-run tests
npm test
npx playwright test tests/pydantic-server-startup.spec.ts
```

## Expected Results After Fix

```
Backend Tests:  51/51 passing (100%)
E2E Tests:      12/12 passing (100%)
Server Status:  Running on port 8001
UI Status:      Green indicator, "Stop" button
```

## Test Coverage Goals

- Server orchestration: 95%+
- Process management: 95%+
- API endpoints: 90%+
- UI workflows: 85%+

## Resources

- **Test Report**: `PYDANTIC_SERVER_TEST_REPORT.md`
- **Fix Guide**: `IMPLEMENTATION_FIXES.md`
- **Completion Summary**: `FUNCTIONAL_TESTING_COMPLETE.md`
