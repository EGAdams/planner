# Start Button Fix - Manual Testing Checklist

## Test Environment
- Dashboard URL: http://localhost:3030
- Dashboard Backend: Running on port 3030
- Browser: Chrome/Firefox with DevTools open

## Pre-Test Setup
1. Ensure dashboard is running: `ps aux | grep "node backend/dist/server.js"`
2. Open browser DevTools (F12)
3. Navigate to Console tab
4. Navigate to http://localhost:3030

## Test Case 1: Initial Page Load
**Objective**: Verify servers load correctly with Start buttons

### Steps
1. Open http://localhost:3030
2. Observe server list in "Managed Servers" section
3. Check browser console for initialization logs

### Expected Results
- [ ] Server list displays 4 servers:
  - Office Assistant API
  - LiveKit Server
  - LiveKit Voice Agent
  - Pydantic Web Server
- [ ] All servers show "Start" button (green)
- [ ] Console shows: "ServerController connected" for each server (4 times)
- [ ] Console shows: "Initial server state fetched" for each server (4 times)
- [ ] No JavaScript errors in console

### Actual Results
_Fill in after testing_

---

## Test Case 2: Start Button Click Response
**Objective**: Verify button shows "Loading..." immediately when clicked

### Steps
1. Identify "Office Assistant API" server
2. Click the "Start" button
3. Observe button state change

### Expected Results (Immediate)
- [ ] Button text changes to "Loading..." within 50ms
- [ ] Spinner animation appears next to "Loading..." text
- [ ] Button becomes disabled (grayed out, cursor changes)
- [ ] Console shows: "toggleServer called" with server object
- [ ] Console shows: "Setting isLoading to true, action: start"

### Expected Results (After API Response)
- [ ] Button changes to "Stop" (red) when server starts successfully
- [ ] OR button shows error message if start fails
- [ ] Loading state disappears
- [ ] Button becomes enabled again

### Actual Results
_Fill in after testing_

---

## Test Case 3: Console Debug Logging
**Objective**: Verify debug logs provide clear information

### Steps
1. Clear browser console (click trash icon)
2. Refresh page
3. Click any "Start" button
4. Review all console messages

### Expected Console Output Sequence
```
1. ServerController connected {serverId: "api-server", apiUrl: "http://localhost:3030"}
2. Attaching click handler to button {serverId: "api-server", buttonText: "Start"}
3. Initial server state fetched {serverId: "api-server", server: {...}}
4. [User clicks button]
5. toggleServer called {isLoading: false, server: {...}}
6. Setting isLoading to true, action: start
7. Attaching click handler to button {serverId: "api-server", buttonText: "Loading..."}
```

### Expected Results
- [ ] No red error messages
- [ ] All logs show proper server data (not null/undefined)
- [ ] Event handler attachment successful
- [ ] API fetch successful

### Actual Results
_Fill in after testing_

---

## Test Case 4: Multiple Servers
**Objective**: Verify all server buttons work independently

### Steps
1. Click "Start" on "Office Assistant API"
2. Immediately click "Start" on "LiveKit Server"
3. Observe both buttons

### Expected Results
- [ ] Both buttons show "Loading..." state
- [ ] Each button operates independently
- [ ] Console shows separate logs for each server
- [ ] No interference between server controls

### Actual Results
_Fill in after testing_

---

## Test Case 5: Error Handling
**Objective**: Verify proper error messages if API fails

### Steps
1. Stop the dashboard backend server
2. Refresh browser page
3. Click any "Start" button

### Expected Results
- [ ] Button shows "Loading..." immediately
- [ ] After timeout, error alert appears
- [ ] Console shows: "Failed to fetch initial server state"
- [ ] Button returns to "Start" state
- [ ] User can try again

### Actual Results
_Fill in after testing_

---

## Test Case 6: EventBus Updates
**Objective**: Verify server state updates from EventBus

### Steps
1. Open two browser tabs to http://localhost:3030
2. In Tab 1, click "Start" on "Office Assistant API"
3. Observe Tab 2

### Expected Results
- [ ] Tab 2 button updates to "Stop" automatically
- [ ] EventBus propagates state changes
- [ ] Both tabs stay in sync

### Actual Results
_Fill in after testing_

---

## Test Case 7: Network Tab Verification
**Objective**: Verify API calls are executed correctly

### Steps
1. Open DevTools → Network tab
2. Filter for "Fetch/XHR"
3. Click "Start" button
4. Observe network requests

### Expected Results
- [ ] Request to `/api/servers` on page load (GET)
- [ ] Request to `/api/servers/api-server?action=start` on button click (POST)
- [ ] Response status 200 (or appropriate error code)
- [ ] Response JSON contains `{success: true/false}`

### Actual Results
_Fill in after testing_

---

## Test Case 8: Rapid Clicks Protection
**Objective**: Verify button can't be clicked repeatedly during loading

### Steps
1. Click "Start" button
2. Immediately click button 5 more times rapidly
3. Observe behavior

### Expected Results
- [ ] Only first click processes
- [ ] Button disabled during loading
- [ ] Console shows: "toggleServer aborted - loading or no server" for subsequent clicks
- [ ] No duplicate API requests

### Actual Results
_Fill in after testing_

---

## Test Case 9: Server Already Running
**Objective**: Verify "Stop" button works correctly

### Steps
1. Start "Office Assistant API" successfully
2. Verify button shows "Stop" (red)
3. Click "Stop" button

### Expected Results
- [ ] Button immediately shows "Loading..."
- [ ] Spinner appears
- [ ] Console shows: "action: stop"
- [ ] After API response, button returns to "Start" (green)

### Actual Results
_Fill in after testing_

---

## Test Case 10: Orphaned Process Handling
**Objective**: Verify "Force Kill" button for orphaned processes

### Steps
1. Start a server outside the dashboard
2. Refresh dashboard to detect orphan
3. Observe orphaned server state
4. Click "Force Kill" button

### Expected Results
- [ ] Orphaned server highlighted in red/orange
- [ ] Button shows "Force Kill" (warning color)
- [ ] Confirmation dialog appears
- [ ] After confirmation, process killed
- [ ] Server returns to stopped state

### Actual Results
_Fill in after testing_

---

## Regression Test: Previous API URL Fix
**Objective**: Verify g50 dynamic API URL still works

### Steps
1. Inspect server-controller element in DevTools
2. Check `api-url` attribute
3. Verify API calls use correct URL

### Expected Results
- [ ] API URL defaults to `window.location.protocol + window.location.host`
- [ ] API calls go to http://localhost:3030
- [ ] No hardcoded URLs in requests

### Actual Results
_Fill in after testing_

---

## Performance Test
**Objective**: Verify page loads quickly with all optimizations

### Steps
1. Open DevTools → Performance tab
2. Start recording
3. Refresh page
4. Click "Start" button
5. Stop recording

### Expected Results
- [ ] Page load < 2 seconds
- [ ] Initial server fetch < 500ms per server
- [ ] Button response < 100ms
- [ ] No layout thrashing
- [ ] No memory leaks

### Actual Results
_Fill in after testing_

---

## Final Verification Checklist

### Core Functionality
- [ ] All buttons respond to clicks immediately
- [ ] Loading states display correctly
- [ ] API calls execute as expected
- [ ] Error handling works properly

### User Experience
- [ ] No confusing delays
- [ ] Clear visual feedback
- [ ] Proper disabled states
- [ ] Helpful error messages

### Code Quality
- [ ] No console errors
- [ ] Proper event listener cleanup
- [ ] Debug logging useful and clear
- [ ] TypeScript compiles without errors

### Integration
- [ ] EventBus updates work
- [ ] Multiple servers operate independently
- [ ] Network requests correct
- [ ] State management consistent

---

## Bug Resolution Confirmation

### Original Issue
**BEFORE FIX**: Start button did not show "Loading..." when clicked

### Fixed Behavior
**AFTER FIX**: Start button immediately shows "Loading..." with spinner

### Root Cause
- Component relied on EventBus for server data
- Server data was null when button clicked before EventBus event fired
- `toggleServer()` returned early without user feedback

### Solution
- Added `fetchInitialServerState()` to fetch server data on component init
- Proper event handler lifecycle management
- Enhanced debug logging

---

## Test Sign-off

**Tester Name**: _________________
**Date**: _________________
**Test Duration**: _________________
**Browser/Version**: _________________
**Result**: PASS / FAIL / PARTIAL

**Notes**:
_Fill in any additional observations_

---

## Cleanup After Testing

Once testing is complete and all cases pass:

1. **Remove Debug Logging**:
   ```bash
   # Edit server-controller.ts and remove console.log statements
   # Rebuild: npm run build
   ```

2. **Commit Changes**:
   ```bash
   git add dashboard/server-controller/server-controller.ts
   git commit -m "Fix Start button regression - immediate Loading state display"
   ```

3. **Optional**: Remove test files
   ```bash
   rm dashboard/test-button.html
   ```

4. **Deploy**: Merge to production branch

---

**Test Document Version**: 1.0
**Last Updated**: 2025-11-15
**Related Fix Report**: START_BUTTON_FIX_REPORT.md
