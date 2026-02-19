#!/bin/bash
# Glintstone v2 — Start Local Development Servers
# Starts uvicorn for API + web, nginx for .test domain routing + marketing static files.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$PROJECT_DIR/.pids"
VENV="$PROJECT_DIR/venv/bin"

mkdir -p "$PID_DIR"

# Load ports from .env (with defaults)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -E '^(API_PORT|WEB_PORT)=' "$PROJECT_DIR/.env" | xargs)
fi
API_PORT=${API_PORT:-8001}
WEB_PORT=${WEB_PORT:-8002}

echo "=== Glintstone v2 ==="
echo ""

# Ensure PostgreSQL PATH
if ! command -v pg_isready &> /dev/null; then
    if [ -d "/opt/homebrew/opt/postgresql@17/bin" ]; then
        export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
    fi
fi

# Check PostgreSQL
if command -v pg_isready &> /dev/null && ! pg_isready -q 2>/dev/null; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@17
    sleep 2
fi

# Check venv exists
if [ ! -f "$VENV/uvicorn" ]; then
    echo "ERROR: venv not found. Run ./ops/local/setup.sh first."
    exit 1
fi

# Stop any existing servers
"$SCRIPT_DIR/stop.sh" 2>/dev/null || true

# Start API (uvicorn with reload for development)
cd "$PROJECT_DIR"
"$VENV/uvicorn" api.main:app --host 127.0.0.1 --port "$API_PORT" --reload > /dev/null 2>&1 &
echo $! > "$PID_DIR/api.pid"

# Start Web (uvicorn with reload)
"$VENV/uvicorn" web.main:app --host 127.0.0.1 --port "$WEB_PORT" --reload > /dev/null 2>&1 &
echo $! > "$PID_DIR/web.pid"

# Start nginx for .test domain routing (port 80 requires sudo)
sudo nginx -c "$SCRIPT_DIR/nginx.conf"

echo "  API:       http://api.glintstone.test"
echo "  API Docs:  http://api.glintstone.test/docs"
echo "  Web App:   http://app.glintstone.test"
echo "  Marketing: http://glintstone.test"
echo ""
echo "Stop: ./ops/local/stop.sh"
echo "Or press Ctrl+C"
echo ""

# Trap Ctrl+C to stop servers
cleanup() {
    echo ""
    "$SCRIPT_DIR/stop.sh"
    exit 0
}
trap cleanup INT TERM

wait
