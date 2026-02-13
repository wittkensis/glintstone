#!/bin/bash
# Stop GLINTSTONE and all dependencies

PROJECT_DIR="/Volumes/Portable Storage/CUNEIFORM"
PID_FILE="$PROJECT_DIR/.glintstone.pid"

echo "Stopping GLINTSTONE services..."
echo ""

# Stop ML service
if [ -f "$PID_FILE" ]; then
    ML_PID=$(cat "$PID_FILE")
    if kill -0 "$ML_PID" 2>/dev/null; then
        echo "✓ Stopping ML service (PID: $ML_PID)"
        kill "$ML_PID"
    else
        echo "✓ ML service already stopped"
    fi
    rm "$PID_FILE"
else
    echo "✓ No ML service PID file found"
fi

# Check for any stray Python processes
ML_PIDS=$(lsof -t -i:8000 2>/dev/null)
if [ -n "$ML_PIDS" ]; then
    echo "✓ Cleaning up port 8000"
    kill $ML_PIDS 2>/dev/null
fi

# Note: We don't stop Valet as it's system-wide
echo ""
echo "✓ Services stopped"
echo ""
echo "Note: Valet web server is still running (system-wide)"
echo "To stop Valet: valet stop"
