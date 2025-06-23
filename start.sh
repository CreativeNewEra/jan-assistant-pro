#!/bin/bash
# Jan Assistant Pro - Smart Launcher Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

echo -e "${BLUE}🚀 Jan Assistant Pro - Smart Launcher${NC}"
echo "================================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if command_exists netstat; then
        netstat -tuln | grep -q ":$port "
    elif command_exists ss; then
        ss -tuln | grep -q ":$port "
    else
        # Fallback: try to connect to the port
        timeout 1 bash -c "</dev/tcp/localhost/$port" 2>/dev/null
    fi
}

# Pre-flight checks
echo "🔍 Running pre-flight checks..."

# Check if config exists
if [ ! -f "config/config.json" ] && [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No configuration found!${NC}"
    echo "Please run the installer first:"
    echo "  python install_wizard.py"
    exit 1
fi

# Check Python version
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found!${NC}"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  ✅ Python $PYTHON_VERSION found"

# Check for virtual environment
VENV_TYPE=""
if [ -f "poetry.lock" ] && command_exists poetry; then
    VENV_TYPE="poetry"
    echo "  ✅ Poetry environment detected"
elif [ -d ".venv" ]; then
    VENV_TYPE="venv"
    echo "  ✅ Virtual environment detected"
elif [ -n "$VIRTUAL_ENV" ]; then
    VENV_TYPE="active"
    echo "  ✅ Active virtual environment detected"
else
    echo -e "${YELLOW}  ⚠️  No virtual environment detected${NC}"
fi

# Check for required modules
echo "🔍 Checking dependencies..."
if [ "$VENV_TYPE" = "poetry" ]; then
    if ! poetry run python -c "import tkinter, requests" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Dependencies missing, installing...${NC}"
        poetry install
    fi
else
    if ! $PYTHON_CMD -c "import tkinter, requests" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Required modules missing!${NC}"
        echo "Please install dependencies:"
        echo "  pip install -r requirements.txt"
        echo "Or run: python install_wizard.py"
        exit 1
    fi
fi
echo "  ✅ Dependencies satisfied"

# Check API endpoints (if configured)
echo "🌐 Checking API connectivity..."
API_STATUS="unknown"

# Try to read API endpoint from config
if [ -f "config/config.json" ]; then
    # Extract base_url using python (more reliable than jq)
    API_URL=$($PYTHON_CMD -c "
import json
try:
    with open('config/config.json') as f:
        config = json.load(f)
    print(config.get('api', {}).get('base_url', ''))
except:
    pass
" 2>/dev/null)
    
    if [ -n "$API_URL" ] && [ "$API_URL" != "your-api-key" ] && [ "$API_URL" != "http://your-api-url" ]; then
        # Extract host and port
        if [[ "$API_URL" =~ http://([^:/]+):([0-9]+) ]]; then
            HOST="${BASH_REMATCH[1]}"
            PORT="${BASH_REMATCH[2]}"
            
            if check_port "$PORT"; then
                echo -e "  ✅ API service available at ${GREEN}$API_URL${NC}"
                API_STATUS="available"
            else
                echo -e "  ${YELLOW}⚠️  API service not responding at $API_URL${NC}"
                API_STATUS="unavailable"
            fi
        else
            echo "  ℹ️  External API configured"
            API_STATUS="external"
        fi
    else
        echo "  ⏭️  API configuration needed"
        API_STATUS="unconfigured"
    fi
fi

# Suggest local services if API is unavailable
if [ "$API_STATUS" = "unavailable" ]; then
    echo ""
    echo -e "${BLUE}💡 Tip: Start a local AI service first:${NC}"
    
    # Check for common local AI services
    if command_exists jan; then
        echo "  • Jan.ai: jan"
    fi
    if check_port 11434; then
        echo -e "  • ${GREEN}Ollama is running${NC} (port 11434)"
    elif command_exists ollama; then
        echo "  • Ollama: ollama serve"
    fi
    if check_port 1234; then
        echo -e "  • ${GREEN}LM Studio is running${NC} (port 1234)"
    fi
    if check_port 5000; then
        echo -e "  • ${GREEN}Text Generation WebUI is running${NC} (port 5000)"
    fi
    
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create data directory if it doesn't exist
mkdir -p data/cache

# Check for existing process
PID_FILE="data/jan-assistant.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Jan Assistant Pro is already running (PID: $OLD_PID)${NC}"
        echo "Stop the existing instance or use a different configuration."
        exit 1
    else
        # Remove stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Start the application
echo ""
echo -e "${GREEN}🚀 Starting Jan Assistant Pro...${NC}"
echo "================================================"

# Choose the right command based on environment
case "$VENV_TYPE" in
    "poetry")
        echo "Using Poetry environment..."
        poetry run python main.py &
        ;;
    "venv")
        echo "Using virtual environment..."
        source .venv/bin/activate
        python main.py &
        ;;
    "active")
        echo "Using active virtual environment..."
        python main.py &
        ;;
    *)
        echo "Using system Python..."
        $PYTHON_CMD main.py &
        ;;
esac

# Store PID for later cleanup
APP_PID=$!
echo $APP_PID > "$PID_FILE"

echo -e "${GREEN}✅ Jan Assistant Pro started successfully!${NC}"
echo "PID: $APP_PID"
echo ""
echo "📝 Logs are available in data/logs/"
echo "🛑 To stop: kill $APP_PID"
echo "🔧 To reconfigure: python install_wizard.py"

# Wait for the application or handle signals
cleanup() {
    echo ""
    echo "🛑 Shutting down Jan Assistant Pro..."
    if kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID"
        wait "$APP_PID" 2>/dev/null
    fi
    rm -f "$PID_FILE"
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for the application to finish
wait "$APP_PID"
rm -f "$PID_FILE"
