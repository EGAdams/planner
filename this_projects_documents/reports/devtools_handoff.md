# Chrome DevTools Bridge – Windows Operator Handoff

You’ll be running the Windows-side setup so our WSL tooling can talk to Chrome through the remote debugging interface. Please work through the steps below and report any output back to Adam.

## 1. Launch Chrome with Remote Debugging

1. Open **Windows PowerShell as Administrator**.
2. Run the helper script that lives in the WSL workspace (adjust the path if the workspace is mapped elsewhere):

   ```powershell
   \\wsl$\Ubuntu-24.04\home\adamsl\planner\scripts\launch_chrome_devtools.bat
   ```

   - Leave the window open while it runs; you should see a message such as “Chrome started with remote debugging port 9222.”
   - If Chrome is already running, close any existing instances first so the remote-debugging flags take effect.

## 2. Verify Firewall Rule and Port

Still in the elevated PowerShell window:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 9222
Get-NetFirewallRule -DisplayName "Chrome MCP Port 9222" -ErrorAction SilentlyContinue
Get-Process chrome | Select-Object Id,Path
```

Please capture the output for each command. We expect:

- `Test-NetConnection` should report `TcpTestSucceeded : True`.
- The firewall rule should exist and be enabled.
- At least one Chrome process path should match `...\Google\Chrome\Application\chrome.exe`.

If the port test fails, rerun the `.bat` file (as admin) to recreate the firewall rule and relaunch Chrome.

## 3. Optional UI Check

Open `http://localhost:9222/json/version` in any Windows browser tab. You should see JSON containing a `webSocketDebuggerUrl`. If you see an error page instead, let Adam know.

> **WSL tip:** When connecting from WSL, `localhost` may not reach the Windows host. Inspect `/etc/resolv.conf` in WSL for the nameserver entry (typically a `172.*` address) and set `MCP_BROWSER_URL=http://<nameserver>:9222` before running `npx chrome-devtools-mcp ...`.

## 4. Keep Chrome Running

Leave the Chrome instance open once the checks pass. Adam will connect from WSL using MCP and will tell you when you can close it.

### Reporting Back

Send Adam the captured PowerShell output (and any errors) so he can continue with the WSL-side setup. Thanks!
