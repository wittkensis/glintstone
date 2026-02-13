#!/bin/bash
# Start GLINTSTONE and all dependencies
# Usage: ./start-glintstone.sh

PROJECT_DIR="/Volumes/Portable Storage/CUNEIFORM"
ML_SERVICE_DIR="$PROJECT_DIR/ml-service"
PID_FILE="$PROJECT_DIR/.glintstone.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Starting GLINTSTONE Development Environment     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Function to check if a port is in use
port_in_use() {
    lsof -i ":$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    if [ -f "$PID_FILE" ]; then
        ML_PID=$(cat "$PID_FILE")
        if kill -0 "$ML_PID" 2>/dev/null; then
            echo "  → Stopping ML service (PID: $ML_PID)"
            kill "$ML_PID"
        fi
        rm "$PID_FILE"
    fi
    echo "Goodbye!"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT TERM

# Step 1: Check Valet
echo -e "${BLUE}[1/4]${NC} Checking web server..."
if ! command -v valet &> /dev/null; then
    echo -e "${RED}✗ Valet not installed${NC}"
    echo "Run ./setup-server.sh first"
    exit 1
fi

# Start Valet if not running
if ! valet status &> /dev/null; then
    echo "  → Starting Valet..."
    valet start
fi
echo -e "${GREEN}✓ Web server running${NC}"
echo ""

# Step 2: Check if site is linked
echo -e "${BLUE}[2/4]${NC} Checking site link..."
if ! valet links | grep -q "glintstone"; then
    echo -e "${YELLOW}⚠ Site not linked yet${NC}"
    echo "  → Linking site..."
    cd "$PROJECT_DIR/app/public_html"
    valet link glintstone
fi
echo -e "${GREEN}✓ Site linked: http://glintstone.test${NC}"
echo ""

# Step 3: Start ML Service
echo -e "${BLUE}[3/4]${NC} Starting ML service..."
if port_in_use 8000; then
    echo -e "${YELLOW}⚠ Port 8000 already in use${NC}"
    echo "  ML service may already be running"
else
    if [ ! -d "$ML_SERVICE_DIR" ]; then
        echo -e "${YELLOW}⚠ ML service directory not found${NC}"
        echo "  Skipping ML service (sign detection won't work)"
    else
        cd "$ML_SERVICE_DIR"

        # Check for Python
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}✗ Python 3 not found${NC}"
            echo "  Install Python 3 to enable sign detection"
        else
            # Start ML service in background
            echo "  → Starting FastAPI server on port 8000..."
            nohup "$ML_SERVICE_DIR/venv/bin/python" app.py > "$PROJECT_DIR/ml-service.log" 2>&1 &
            ML_PID=$!
            echo $ML_PID > "$PID_FILE"

            # Wait a moment and check if it started
            sleep 2
            if kill -0 "$ML_PID" 2>/dev/null; then
                echo -e "${GREEN}✓ ML service running (PID: $ML_PID)${NC}"
                echo "  Logs: $PROJECT_DIR/ml-service.log"
            else
                echo -e "${RED}✗ ML service failed to start${NC}"
                echo "  Check logs: $PROJECT_DIR/ml-service.log"
                rm "$PID_FILE"
            fi
        fi
    fi
fi
echo ""

# Step 4: Open browser
echo -e "${BLUE}[4/4]${NC} Opening browser..."
if command -v open &> /dev/null; then
    open "http://glintstone.test"
    echo -e "${GREEN}✓ Browser opened${NC}"
else
    echo "  Open manually: http://glintstone.test"
fi
echo ""

# Show status
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    ✓ GLINTSTONE READY                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Main Site:${NC}       http://glintstone.test"
echo -e "${GREEN}Tablet View:${NC}     http://glintstone.test/tablets/detail.php?p=P388097"
echo -e "${GREEN}Dictionary:${NC}      http://glintstone.test/dictionary/"
echo -e "${GREEN}ML Detection:${NC}    http://glintstone.test/api/ml/detect-signs.php?p=P388097"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo "  valet status      - Check web server"
echo "  valet restart     - Restart web server"
echo "  tail -f ml-service.log  - View ML service logs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
if [ -f "$PID_FILE" ]; then
    echo "Monitoring services..."
    while true; do
        sleep 5
        # Check if ML service is still running
        ML_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$ML_PID" ] && ! kill -0 "$ML_PID" 2>/dev/null; then
            echo -e "${RED}⚠ ML service stopped unexpectedly${NC}"
            rm "$PID_FILE"
            break
        fi
    done
else
    echo "Web server is running. Press Ctrl+C to exit."
    # Just wait indefinitely
    tail -f /dev/null
fi
