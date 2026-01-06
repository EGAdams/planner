#!/bin/bash

###############################################################################
# Receipt Scanner Startup Script
# Starts all necessary components for the receipt scanning system
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "$PROJECT_DIR")")"
ENV_FILE="$PARENT_DIR/.env"
API_PORT=${API_PORT:-8080}
LETTA_PORT=${LETTA_PORT:-8283}
API_LOG_FILE="/tmp/receipt_scanner_api.log"
LETTA_LOG_FILE="/tmp/receipt_scanner_letta.log"

# Track PIDs for cleanup
API_PID=""
LETTA_PID=""

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function called on exit
cleanup() {
    log_info "Shutting down services..."

    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        log_info "Stopping API server (PID: $API_PID)..."
        kill "$API_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$API_PID" 2>/dev/null || true
    fi

    if [ -n "$LETTA_PID" ] && kill -0 "$LETTA_PID" 2>/dev/null; then
        log_info "Stopping Letta server (PID: $LETTA_PID)..."
        kill "$LETTA_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$LETTA_PID" 2>/dev/null || true
    fi

    log_success "Shutdown complete"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

###############################################################################
# Pre-flight Checks
###############################################################################

check_environment() {
    log_info "Checking environment setup..."

    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found at $ENV_FILE"
        log_warning "Please create .env with required variables:"
        log_warning "  GEMINI_API_KEY"
        log_warning "  DB_HOST (default: 127.0.0.1)"
        log_warning "  DB_PORT (default: 3306)"
        log_warning "  NON_PROFIT_USER"
        log_warning "  NON_PROFIT_PASSWORD"
        log_warning "  NON_PROFIT_DB_NAME"
        exit 1
    fi

    log_success "Environment file found"
}

check_python() {
    log_info "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python $PYTHON_VERSION found"
}

check_dependencies() {
    log_info "Checking Python dependencies..."

    cd "$PROJECT_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$PROJECT_DIR/venv"
        log_success "Virtual environment created"
    fi

    # Check if we can import required modules
    if "$PROJECT_DIR/venv/bin/python" -c "import fastapi" 2>/dev/null; then
        log_success "Dependencies already installed"
        return 0
    fi

    log_warning "Dependencies not installed. Installing now..."

    if [ -f "$PROJECT_DIR/receipt_scanner/requirements.txt" ]; then
        "$PROJECT_DIR/venv/bin/pip" install -q -r "$PROJECT_DIR/receipt_scanner/requirements.txt"
        log_success "Dependencies installed"
    else
        log_warning "requirements.txt not found at $PROJECT_DIR/receipt_scanner/requirements.txt"
    fi
}

check_mysql() {
    log_info "Checking MySQL connection..."

    # Source the .env file to get database credentials
    source "$ENV_FILE"

    DB_HOST=${DB_HOST:-127.0.0.1}
    DB_PORT=${DB_PORT:-3306}
    NON_PROFIT_USER=${NON_PROFIT_USER:-root}

    # Try to connect to MySQL
    if command -v mysql &> /dev/null; then
        if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$NON_PROFIT_USER" -p"$NON_PROFIT_PASSWORD" \
            -e "SELECT 1;" &>/dev/null; then
            log_success "MySQL connection OK"
            return 0
        fi
    fi

    log_warning "Could not verify MySQL connection"
    log_warning "Make sure MySQL is running and credentials in .env are correct"
    log_warning "Continuing anyway - API will fail if database is unavailable"
}

check_directories() {
    log_info "Checking required directories..."

    mkdir -p "$PROJECT_DIR/data/receipts/temp"
    mkdir -p "/tmp/receipt_uploads"

    log_success "Directories ready"
}

###############################################################################
# Service Startup Functions
###############################################################################

start_api_server() {
    log_info "Starting API server on port $API_PORT..."

    # API server must run from parent directory (nonprofit_finance_db) to find 'app' module
    cd "$PARENT_DIR"

    # Start the API server in background (use venv Python if available)
    local python_cmd="python3"
    if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
        python_cmd="$PROJECT_DIR/venv/bin/python"
    fi

    $python_cmd receipt_scanning_tools/server_tools/api_server.py > "$API_LOG_FILE" 2>&1 &
    API_PID=$!

    # Wait for API to start and check if it's running
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if kill -0 "$API_PID" 2>/dev/null; then
            # Process is running, check if port is listening
            if curl -s "http://localhost:$API_PORT/health" >/dev/null 2>&1 || \
               curl -s "http://localhost:$API_PORT/api/receipts" >/dev/null 2>&1; then
                log_success "API server started (PID: $API_PID) on port $API_PORT"
                return 0
            fi
        else
            log_error "API server failed to start"
            log_error "See logs at: $API_LOG_FILE"
            cat "$API_LOG_FILE"
            exit 1
        fi

        sleep 1
        attempt=$((attempt + 1))
    done

    log_warning "API server started but health check timeout"
    log_warning "Server may still be initializing. Check: $API_LOG_FILE"
}

start_letta_server() {
    local start_letta=${1:-false}

    if [ "$start_letta" = false ]; then
        return 0
    fi

    log_info "Starting Letta server on port $LETTA_PORT..."

    if ! command -v letta &> /dev/null; then
        log_warning "Letta not installed. Skipping Letta server."
        log_warning "To enable agent features, install Letta: pip install letta"
        return 0
    fi

    letta server --port "$LETTA_PORT" > "$LETTA_LOG_FILE" 2>&1 &
    LETTA_PID=$!

    # Wait for Letta to start
    sleep 3

    if kill -0 "$LETTA_PID" 2>/dev/null; then
        log_success "Letta server started (PID: $LETTA_PID) on port $LETTA_PORT"
    else
        log_warning "Letta server may have failed to start"
        log_warning "See logs at: $LETTA_LOG_FILE"
    fi
}

open_browser() {
    local url="http://localhost:$API_PORT/receipt-scanner"

    log_info "Opening receipt scanner in browser..."

    if command -v xdg-open &> /dev/null; then
        xdg-open "$url" 2>/dev/null &
        log_success "Browser opened to $url"
    elif command -v open &> /dev/null; then
        open "$url" 2>/dev/null &
        log_success "Browser opened to $url"
    else
        log_warning "Could not open browser automatically"
        log_info "Open manually: $url"
    fi
}

show_status() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Receipt Scanner Started Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo "  API Server:      http://localhost:$API_PORT"
    echo "  Receipt Scanner: http://localhost:$API_PORT/receipt-scanner"

    if [ -n "$LETTA_PID" ] && kill -0 "$LETTA_PID" 2>/dev/null; then
        echo "  Letta Server:    http://localhost:$LETTA_PORT"
    fi

    echo ""
    echo -e "${BLUE}Logs:${NC}"
    echo "  API:   $API_LOG_FILE"
    if [ -n "$LETTA_PID" ] && kill -0 "$LETTA_PID" 2>/dev/null; then
        echo "  Letta: $LETTA_LOG_FILE"
    fi

    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  View API logs:    tail -f $API_LOG_FILE"
    echo "  Stop services:    Ctrl+C"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
}

###############################################################################
# Main Script
###############################################################################

main() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}Receipt Scanner Startup${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""

    # Parse arguments
    START_LETTA=false
    OPEN_BROWSER=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-letta)
                START_LETTA=true
                shift
                ;;
            --no-browser)
                OPEN_BROWSER=false
                shift
                ;;
            --port)
                API_PORT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --with-letta      Start Letta agent server (requires letta installation)"
                echo "  --no-browser      Don't open browser automatically"
                echo "  --port PORT       Use custom API port (default: 8080)"
                echo "  --help            Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run pre-flight checks
    check_environment
    check_python
    check_dependencies
    check_directories
    check_mysql

    echo ""

    # Start services
    start_api_server
    start_letta_server "$START_LETTA"

    echo ""

    # Open browser if requested
    if [ "$OPEN_BROWSER" = true ]; then
        sleep 2  # Give API time to fully initialize
        open_browser
    fi

    # Show status
    show_status

    # Keep script running
    wait "$API_PID" 2>/dev/null || true
}

main "$@"
