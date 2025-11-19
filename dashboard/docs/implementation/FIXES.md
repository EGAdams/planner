# Pydantic Server Startup - Implementation Fixes

## Overview
This document provides the implementation fixes required to make the Pydantic server start successfully.

## Fix Implementation

### Fix #1: Replace UV Command with Python Venv

**File**: `/home/adamsl/planner/dashboard/backend/server.ts`  
**Lines**: 51-57

**Current Code**:
```typescript
'pydantic-web-server': {
  name: 'Pydantic Web Server',
  command: 'uv run python pydantic_mcp_agent_endpoint.py',
  cwd: '/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version',
  color: '#E9D5FF',
  ports: [8001],
},
```

**Fixed Code**:
```typescript
'pydantic-web-server': {
  name: 'Pydantic Web Server',
  command: '/home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py',
  cwd: '/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version',
  color: '#E9D5FF',
  ports: [8001],
  env: {
    ...process.env,
    PYTHONPATH: '/home/adamsl/planner/venv/lib/python3.12/site-packages'
  }
},
```

### Fix #2: Update Old Test Port Reference

**File**: `/home/adamsl/planner/dashboard/tests/managed-servers.spec.ts`  
**Lines**: 209-214

**Current Code**:
```typescript
// Verify the server is listening on port 8000
await page.waitForTimeout(2000); // Give it time to bind to port
const portsResponse = await page.request.get(API_URL + '/ports');
const ports = await portsResponse.json();
const port8000 = ports.find((p: any) => p.port === '8000');
expect(port8000).toBeTruthy();
```

**Fixed Code**:
```typescript
// Verify the server is listening on port 8001
await page.waitForTimeout(2000); // Give it time to bind to port
const portsResponse = await page.request.get(API_URL + '/ports');
const ports = await portsResponse.json();
const port8001 = ports.find((p: any) => p.port === '8001');
expect(port8001).toBeTruthy();
```

### Fix #3: Create Environment Configuration

**File**: `/home/adamsl/planner/.env` (create if doesn't exist)

```bash
# Pydantic Server Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
API_BEARER_TOKEN=your-bearer-token-here

# Admin Dashboard Configuration
ADMIN_PORT=3030
ADMIN_HOST=127.0.0.1
SUDO_PASSWORD=your-sudo-password
```

**Note**: Update with actual credentials from Supabase dashboard

### Fix #4: Install Python Dependencies

If dependencies are not installed in the venv, run:

```bash
cd /home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version
/home/adamsl/planner/venv/bin/pip install -r requirements.txt
```

**Note**: The requirements.txt file appears to have encoding issues. May need to recreate it.

---

## Alternative Fix: Install UV Package Manager

If you prefer to use `uv` as originally intended:

```bash
# Download UV installer
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh

# Review the script
cat /tmp/uv-install.sh

# Install (after review)
sh /tmp/uv-install.sh

# Add to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

Then revert server.ts to use original command: `uv run python pydantic_mcp_agent_endpoint.py`

---

## Verification Steps

After applying fixes:

1. **Rebuild Backend**:
   ```bash
   cd /home/adamsl/planner/dashboard
   npm run build:backend
   ```

2. **Start Dashboard Server**:
   ```bash
   npm run dev:backend
   ```

3. **Test Pydantic Server Startup**:
   ```bash
   curl -X POST http://localhost:3030/api/servers/pydantic-web-server?action=start
   ```

4. **Verify Port Listening**:
   ```bash
   lsof -i :8001
   ```

5. **Test Endpoint**:
   ```bash
   curl http://localhost:8001/docs
   ```

6. **Run Tests**:
   ```bash
   # Backend tests
   npm test

   # E2E tests
   npx playwright test tests/pydantic-server-startup.spec.ts
   ```

---

## Expected Test Results After Fixes

### Jest Tests:
- ✓ All 37 backend tests should pass
- Note: Integration tests expecting live server should be moved to separate suite

### Playwright Tests:
- ✓ 12/12 Pydantic startup tests should pass
- ✓ Server starts successfully
- ✓ Port 8001 listening
- ✓ UI updates correctly
- ✓ Health monitoring works

---

## Rollback Plan

If fixes cause issues:

1. **Revert server.ts changes**:
   ```bash
   git checkout backend/server.ts
   ```

2. **Stop all servers**:
   ```bash
   curl -X POST http://localhost:3030/api/servers/pydantic-web-server?action=stop
   ```

3. **Review logs**:
   ```bash
   # Check dashboard server logs
   # Check for errors in browser console
   ```

---

## Additional Recommendations

1. **Create Startup Script**: Consider creating `/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version/start.sh`:
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   exec /home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py
   ```

2. **Add Health Check Endpoint**: The Pydantic server should have a `/health` endpoint for monitoring

3. **Logging**: Add proper logging to track startup issues

4. **Documentation**: Update README with startup procedures

---

**Status**: FIXES DOCUMENTED - READY FOR IMPLEMENTATION  
**Risk Level**: LOW (using existing venv, minimal changes)  
**Estimated Time**: 15 minutes to apply fixes and verify
