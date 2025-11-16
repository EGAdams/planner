#!/usr/bin/env bash
set -euo pipefail

PORT="${CHROME_DEVTOOLS_PORT:-9222}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to auto-start Chrome for MCP. Please install python3 or set MCP_BROWSER_URL to a running Chrome instance." >&2
  exit 1
fi

chrome_pid=""
cleanup_local_chrome() {
  if [[ -n "${chrome_pid:-}" ]]; then
    kill "${chrome_pid}" >/dev/null 2>&1 || true
    wait "${chrome_pid}" >/dev/null 2>&1 || true
    chrome_pid=""
  fi
}
trap cleanup_local_chrome EXIT

is_local_address() {
  local host="${1:-}"
  case "${host}" in
    ""|127.0.0.1|localhost|0.0.0.0|::1) return 0 ;;
    *) return 1 ;;
  esac
}

port_is_open() {
  local host="$1"
  local port="$2"

  if [[ -z "${host}" || -z "${port}" ]]; then
    return 1
  fi

  if PORT_CHECK_HOST="${host}" PORT_CHECK_PORT="${port}" python3 <<'PY'
import os, socket, sys

host = os.environ["PORT_CHECK_HOST"]
port = int(os.environ["PORT_CHECK_PORT"])

sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
  then
    return 0
  else
    return 1
  fi
}

wait_for_port_open() {
  local host="$1"
  local port="$2"
  local timeout="${3:-10}"
  local start="${SECONDS}"

  while ! port_is_open "${host}" "${port}"; do
    if (( SECONDS - start >= timeout )); then
      return 1
    fi
    sleep 0.2
  done
}

find_chrome_binary() {
  if [[ -n "${CHROME_BINARY:-}" ]]; then
    if [[ -x "${CHROME_BINARY}" ]]; then
      printf '%s\n' "${CHROME_BINARY}"
      return 0
    fi
    echo "CHROME_BINARY=${CHROME_BINARY} is not executable" >&2
    return 1
  fi

  local candidates=(google-chrome-stable google-chrome chromium-browser chromium brave-browser)
  local path
  for candidate in "${candidates[@]}"; do
    if path="$(command -v "${candidate}" 2>/dev/null)"; then
      printf '%s\n' "${path}"
      return 0
    fi
  done

  return 1
}

start_local_chrome() {
  local port="$1"
  local host="${2:-127.0.0.1}"
  local chrome_binary

  if ! chrome_binary="$(find_chrome_binary)"; then
    echo "Unable to locate a Chrome binary for remote debugging. Install Chrome or set CHROME_BINARY to override." >&2
    return 1
  fi

  local profile_dir="${CHROME_PROFILE_DIR:-${HOME:-/tmp}/.cache/mcp-chrome-profile-${port}}"
  mkdir -p "${profile_dir}"

  local headless_setting="${CHROME_HEADLESS:-1}"
  local headless_args=()
  if [[ ! "${headless_setting,,}" =~ ^(0|false)$ ]]; then
    headless_args=(--headless=new --disable-gpu)
  fi

  local chrome_args=(
    "--remote-debugging-port=${port}"
    "--remote-debugging-address=127.0.0.1"
    "--remote-allow-origins=*"
    "--user-data-dir=${profile_dir}"
    "--no-first-run"
    "--disable-background-networking"
    "--disable-background-timer-throttling"
    "--disable-component-extensions-with-background-pages"
    "--disable-default-apps"
    "--disable-extensions"
    "--disable-notifications"
    "--disable-plugins"
    "--disable-plugins-discovery"
    "--disable-translate"
    "--disable-sync"
    "--disable-software-rasterizer"
    "${headless_args[@]}"
  )

  echo "Launching Chrome (${chrome_binary}) to expose remote debugging on ${host}:${port}..." >&2
  "${chrome_binary}" "${chrome_args[@]}" >/dev/null 2>&1 &
  chrome_pid=$!

  if ! wait_for_port_open "${host}" "${port}" 10; then
    echo "Chrome did not open debugging port ${port} in time." >&2
    cleanup_local_chrome
    return 1
  fi

  echo "Chrome is listening on ${host}:${port} (PID ${chrome_pid})." >&2
}

resolve_nameserver() {
  if [[ -r /etc/resolv.conf ]]; then
    awk '/^nameserver/ { print $2; exit }' /etc/resolv.conf 2>/dev/null || true
  fi
}

BROWSER_URL=""
if [[ -n "${MCP_BROWSER_URL:-}" ]]; then
  BROWSER_URL="${MCP_BROWSER_URL}"
else
  if [[ -r /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    nameserver="$(resolve_nameserver)"
    if [[ -n "${nameserver:-}" ]]; then
      BROWSER_URL="http://${nameserver}:${PORT}"
    fi
  fi

  if [[ -z "${BROWSER_URL}" ]]; then
    BROWSER_URL="http://127.0.0.1:${PORT}"
  fi
fi

if ! BROWSER_HOST_PORT="$(PORT_DEFAULT="${PORT}" python3 <<'PY'
import os
import urllib.parse

url = os.environ["BROWSER_URL"]
port_default = int(os.environ["PORT_DEFAULT"])
parsed = urllib.parse.urlparse(url)
host = parsed.hostname or "127.0.0.1"
port = parsed.port or port_default
print(host, port)
PY
)"; then
  echo "Unable to parse browser URL: ${BROWSER_URL}" >&2
  exit 1
fi

read -r BROWSER_HOST BROWSER_PORT <<<"${BROWSER_HOST_PORT}"

if is_local_address "${BROWSER_HOST}" && ! port_is_open "${BROWSER_HOST}" "${BROWSER_PORT}"; then
  if ! start_local_chrome "${BROWSER_PORT}" "${BROWSER_HOST}"; then
    echo "Failed to launch Chrome for MCP." >&2
    exit 1
  fi
fi

echo "Starting Chrome DevTools MCP using ${BROWSER_URL}" >&2
npx -y chrome-devtools-mcp --browser-url "${BROWSER_URL}"
