#!/bin/bash
set -euo pipefail

# This script launches the native Windows Chrome with a remote-debugging port so
# that chrome-devtools-mcp (running inside WSL) can connect without needing to
# spawn a sandboxed browser. Run with sudo from your WSL shell.

if [[ "${EUID}" -ne 0 ]]; then
  echo "Warning: running without sudo. Firewall changes may fail if elevated privileges are required on Windows." >&2
fi

PORT="${1:-9222}"
PROFILE_DIR_NAME="MCPChromeProfile"
POWERSHELL_PATH=""
for candidate in \
  "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe" \
  "/mnt/c/Windows/System32/powershell.exe" \
  "/mnt/c/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"; do
  if [[ -x "${candidate}" ]]; then
    POWERSHELL_PATH="${candidate}"
    break
  fi
done

if [[ -z "${POWERSHELL_PATH}" ]]; then
  echo "Unable to locate powershell.exe. Ensure Windows system files are mounted inside WSL." >&2
  exit 1
fi

POWERSHELL=("${POWERSHELL_PATH}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command)

tmp_ps1="$(mktemp --suffix=.ps1)"
trap 'rm -f "${tmp_ps1}"' EXIT

cat > "${tmp_ps1}" <<'EOF'
param(
  [Parameter(Mandatory = $true)][int]$Port,
  [Parameter(Mandatory = $true)][string]$ProfileName
)

$chromePath64 = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$chromePath32 = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

if (Test-Path -LiteralPath $chromePath64) {
  $chromePath = $chromePath64
} elseif (Test-Path -LiteralPath $chromePath32) {
  $chromePath = $chromePath32
} else {
  Write-Error 'Unable to locate chrome.exe. Please install Google Chrome on Windows.' -ErrorAction Stop
}

$ruleName = "Chrome MCP Port $Port"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
}

$profilePath = Join-Path $env:LOCALAPPDATA $ProfileName
if (-not (Test-Path -LiteralPath $profilePath)) {
  New-Item -ItemType Directory -Path $profilePath | Out-Null
}

Start-Process -FilePath $chromePath -ArgumentList @(
  "--remote-debugging-port=$Port",
  "--remote-allow-origins=*",
  "--user-data-dir=$profilePath",
  "--no-first-run",
  "--disable-background-networking",
  "--disable-default-apps"
) | Out-Null
EOF

"${POWERSHELL[@]}" "& '${tmp_ps1}' -Port ${PORT} -ProfileName '${PROFILE_DIR_NAME}'" >/dev/null

WSL_HOME="$(eval echo ~${SUDO_USER:-$USER})"
cat <<EOF
Chrome has been started on Windows with remote debugging port ${PORT}.

In your WSL shell, you can now run:

  export MCP_BROWSER_URL=http://127.0.0.1:${PORT}
  cd /home/adamsl/planner
  npx chrome-devtools-mcp@latest --browser-url "\${MCP_BROWSER_URL}"

This reuses the Windows browser and avoids the sandbox limitations inside WSL.
The first npx call will download the package if required.
Chrome profile data is isolated in %LOCALAPPDATA%\\${PROFILE_DIR_NAME}.
EOF
