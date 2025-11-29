#!/usr/bin/env bash
set -euo pipefail

# Paths
LOG_DIR="$HOME/planner/logs"

LIVEKIT_BIN="/home/adamsl/ottomator-agents/livekit-agent/livekit-server"
LIVEKIT_VENV="/home/adamsl/planner/livekit-venv/bin/activate"
LIVEKIT_PORT=7880
LIVEKIT_LOG="$LOG_DIR/livekit-server.log"
LIVEKIT_PID="$LOG_DIR/livekit-server.pid"

LETTA_VENV="/home/adamsl/planner/.venv/bin/activate"
LETTA_ENV="$HOME/planner/.env"
LETTA_PORT=8283
LETTA_LOG="$LOG_DIR/letta-server.log"
LETTA_PID="$LOG_DIR/letta-server.pid"

mkdir -p "$LOG_DIR"

is_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$port )" | grep -q ":$port"
  else
    lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1
  fi
}

start_livekit() {
  if is_listening "$LIVEKIT_PORT"; then
    echo "LiveKit already listening on :$LIVEKIT_PORT"
    return
  fi

  if [[ ! -x "$LIVEKIT_BIN" ]]; then
    echo "LiveKit binary not found at $LIVEKIT_BIN" >&2
    exit 1
  fi

  # shellcheck source=/dev/null
  source "$LIVEKIT_VENV"
  pushd "$(dirname "$LIVEKIT_BIN")" >/dev/null
  nohup "$LIVEKIT_BIN" --dev --bind 0.0.0.0 >"$LIVEKIT_LOG" 2>&1 &
  echo $! >"$LIVEKIT_PID"
  popd >/dev/null
  echo "Started LiveKit (pid $(cat "$LIVEKIT_PID")) on :$LIVEKIT_PORT"
}

start_letta() {
  if is_listening "$LETTA_PORT"; then
    echo "Letta already listening on :$LETTA_PORT"
    return
  fi

  # shellcheck source=/dev/null
  source "$LETTA_VENV"
  # shellcheck source=/dev/null
  source "$LETTA_ENV"
  nohup letta server --port "$LETTA_PORT" >"$LETTA_LOG" 2>&1 &
  echo $! >"$LETTA_PID"
  echo "Started Letta (pid $(cat "$LETTA_PID")) on :$LETTA_PORT"
}

start_livekit
start_letta
