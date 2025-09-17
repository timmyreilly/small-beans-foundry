#!/bin/bash

# Stop all development servers for agentic-ui-v0

echo "Stopping Agentic UI v0 Development Environment..."

# Kill all related processes
echo "Terminating application processes..."

# Kill backend processes
pkill -f "uvicorn.*main:app" 2>/dev/null

# Kill frontend processes  
pkill -f "vite" 2>/dev/null
pkill -f "tsx.*server.ts" 2>/dev/null
pkill -f "concurrently" 2>/dev/null

# Kill any remaining processes on our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sleep 2

echo "✅ All development servers stopped"
echo ""
echo "To restart, run: ./start-dev.sh"