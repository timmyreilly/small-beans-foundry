#!/bin/bash

# Agentic UI v0 Development Startup Script
echo "🚀 Starting Agentic UI v0 Development Environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ Node.js/npm is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup complete"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start backend
echo "🔧 Starting backend (FastAPI)..."
cd backend

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing/updating backend dependencies..."
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please configure your Azure settings in backend/.env"
fi

# Start backend server
echo "🚀 Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Start frontend
echo "🔧 Starting frontend (Vue.js)..."
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend development server
echo "🚀 Starting Vue.js development server on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

cd ..

# Display information
echo ""
echo "🎉 Agentic UI v0 Development Environment Started!"
echo ""
echo "📊 Services running:"
echo "   🔗 Frontend (Vue.js):  http://localhost:5173"
echo "   🔗 Backend (FastAPI):   http://localhost:8000"
echo "   🔗 API Documentation:   http://localhost:8000/docs"
echo "   🔗 Health Check:        http://localhost:8000/health"
echo ""
echo "⚙️  Configuration:"
echo "   📁 Backend config:      backend/.env"
echo "   📁 Frontend proxy:      Vite dev server -> :8000/api"
echo ""
echo "🔧 To stop the servers, press Ctrl+C"
echo ""

# Wait for user to stop
wait