setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=9222"

set "PROFILE_NAME=MCPChromeProfile"

echo Launching Chrome DevTools helper on Windows...

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "& {param($Port,$ProfileName) ^
      $chromePaths = @('C:\Program Files\Google\Chrome\Application\chrome.exe', 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'); ^
      $chromePath = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1; ^
      if (-not $chromePath) { Write-Error 'Cannot find chrome.exe. Please install Google Chrome.'; exit 1 } ^
      $ruleName = \"Chrome MCP Port $Port\"; ^
      if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) { ^
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null ^
      } ^
      $profilePath = Join-Path $env:LOCALAPPDATA $ProfileName; ^
      if (-not (Test-Path $profilePath)) { ^
        New-Item -ItemType Directory -Path $profilePath | Out-Null ^
      } ^
      Start-Process -FilePath $chromePath -ArgumentList @(
        \"--remote-debugging-port=$Port\",
        \"--remote-allow-origins=*\",
        \"--user-data-dir=$profilePath\",
        \"--no-first-run\",
        \"--disable-background-networking\",
        \"--disable-default-apps\"
      ) ^
    }" -Port %PORT% -ProfileName %PROFILE_NAME%

if errorlevel 1 (
  echo Failed to launch Chrome. See the PowerShell output above for details.
) else (
  echo Chrome started with remote debugging port %PORT%.
  echo Leave this window running while you connect from WSL using:
  echo   export MCP_BROWSER_URL=http://127.0.0.1:%PORT%
  echo   npx -y chrome-devtools-mcp --browser-url "%%MCP_BROWSER_URL%%"
)

endlocal
