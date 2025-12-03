#!/bin/bash
# Restart the Letta server and tail the most recent log output location.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PLANNER_ROOT/.env"
LOG_DIR="$PLANNER_ROOT/logs"
LOG_FILE="$LOG_DIR/letta.log"
PID_FILE="$LOG_DIR/letta.pid"
PORT=8283

mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment variables so the Letta server sees database + API keys.
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}Warning: $ENV_FILE not found; continuing with current environment.${NC}"
fi

DEFAULT_PG_URI="postgresql+asyncpg://letta:letta@localhost:5432/letta"
if [ -z "${LETTA_PG_URI:-}" ]; then
    echo "LETTA_PG_URI not set; defaulting to $DEFAULT_PG_URI"
    export LETTA_PG_URI="$DEFAULT_PG_URI"
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo -e "${RED}OPENAI_API_KEY is not set. Update .env or export it before restarting.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Restarting Letta Server ===${NC}"
echo "Workspace: $PLANNER_ROOT"
echo "Log file: $LOG_FILE"
echo ""

stop_existing_server() {
    local stopped=0

    if command -v lsof >/dev/null 2>&1; then
        mapfile -t port_pids < <(lsof -ti:"$PORT" 2>/dev/null || true)
    else
        port_pids=()
    fi

    if [ "${#port_pids[@]}" -eq 0 ] && command -v ss >/dev/null 2>&1; then
        mapfile -t port_pids < <(ss -lptn 2>/dev/null | grep ":$PORT " | awk -F',' '{print $2}' | cut -d'=' -f2 || true)
    fi

    if pgrep -f "letta server" >/dev/null 2>&1; then
        mapfile -t proc_pids < <(pgrep -f "letta server" || true)
        port_pids+=("${proc_pids[@]}")
    fi

    for pid in "${port_pids[@]:-}"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            stopped=1
            echo -e "${YELLOW}Stopping Letta PID $pid...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done

    if [ "$stopped" -eq 1 ]; then
        sleep 1
        for pid in "${port_pids[@]:-}"; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Force killing PID $pid...${NC}"
                kill -9 "$pid" 2>/dev/null || true
            fi
        done
    else
        echo -e "${YELLOW}No existing Letta server found on port $PORT${NC}"
    fi
}

find_letta_command() {
    if [ -x "$PLANNER_ROOT/.venv/bin/letta" ]; then
        echo "$PLANNER_ROOT/.venv/bin/letta server"
    elif command -v letta >/dev/null 2>&1; then
        echo "letta server"
    elif [ -x "$PLANNER_ROOT/.venv/bin/python" ]; then
        echo "$PLANNER_ROOT/.venv/bin/python -m letta server"
    else
        echo "python3 -m letta server"
    fi
}

start_server() {
    local letta_cmd
    letta_cmd="$(find_letta_command)"

    echo -e "${GREEN}Starting Letta server...${NC}"
    (
        cd "$PLANNER_ROOT"
        nohup $letta_cmd > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
    )
    LETTA_PID="$(cat "$PID_FILE")"
    echo "PID: $LETTA_PID"

    sleep 3
    if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1 || curl -sf "http://localhost:$PORT/v1/health" >/dev/null 2>&1; then
        echo -e "${GREEN}Letta API responded successfully.${NC}"
    else
        echo -e "${YELLOW}Letta API not responding yet. Check the log for details.${NC}"
        tail -n 40 "$LOG_FILE"
    fi
}

stop_existing_server
start_server

echo ""
echo -e "${GREEN}Restart complete.${NC}"
echo "View logs with: tail -f $LOG_FILE"
