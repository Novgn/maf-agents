#!/bin/bash

# Development script for MAF Agents monorepo
# Properly handles Ctrl+C to shut down both servers

set -e

# Colors for output
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Cleanup function to kill all child processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

echo "🚀 Starting MAF Agents in development mode..."
echo ""

# Get the root directory
ROOT_DIR=$(pwd)

# Start backend server
echo "${BLUE}[API]${NC} Starting FastAPI server on http://localhost:8000"
(cd "$ROOT_DIR/server" && uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000) 2>&1 | sed "s/^/${BLUE}[API]${NC} /" &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Start frontend
echo "${MAGENTA}[UI]${NC} Starting Next.js client on http://localhost:3000"
(cd "$ROOT_DIR/client" && npm run dev) 2>&1 | sed "s/^/${MAGENTA}[UI]${NC} /" &
CLIENT_PID=$!

# Wait for both processes
wait $SERVER_PID $CLIENT_PID
