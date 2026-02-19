#!/bin/bash
# Glintstone v2 — Stop Local Development Servers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$PROJECT_DIR/.pids"

echo "Stopping Glintstone v2..."

for pidfile in "$PID_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    pid=$(cat "$pidfile")
    name=$(basename "$pidfile" .pid)
    if kill "$pid" 2>/dev/null; then
        echo "  Stopped $name (PID $pid)"
    fi
    rm -f "$pidfile"
done

# Stop nginx (.test domain routing)
NGINX_PID="/tmp/glintstone-nginx.pid"
if [ -f "$NGINX_PID" ]; then
    sudo nginx -s stop -c "$SCRIPT_DIR/nginx.conf" 2>/dev/null && echo "  Stopped nginx" || true
    rm -f "$NGINX_PID"
fi

echo "Done. PostgreSQL left running (brew services stop postgresql@17 to stop)."
