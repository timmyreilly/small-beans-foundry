# Agentic UI v0

A simplified full-stack conversational AI application with Vue.js frontend and FastAPI backend powered by **Microsoft AutoGen** with Azure AI Foundry integration.

## Overview

A clean foundation for AutoGen integration while maintaining essential scaffolding and configuration patterns.

## Architecture

- **Frontend**: Vue.js 3 with TypeScript, Pinia for state management
- **Backend**: FastAPI with **single AutoGen Azure AI Agent**
- **AI Service**: Microsoft AutoGen with Azure AI Foundry project
- **Communication**: RESTful API with CORS configuration

## Quick Start

### Prerequisites

- Node.js (v18+)
- Python (v3.10+) - AutoGen requirement
- Azure AI Foundry project with API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd agentic-ui-v0
   ```

2. **Configure Azure AI Foundry:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your Azure AI Foundry configuration
   cd ..
   ```

3. **Start development environment:**
   ```bash
   ./start-dev.sh
   ```

### Azure Configuration

Update `backend/.env` with your Azure AI Foundry details:

See

```env
# Your Azure AI Foundry project endpoint
AZURE_PROJECT_ENDPOINT=https://your-foundry-resource.services.ai.azure.com/api/projects/YourProjectName

# Your API key
AZURE_FOUNDRY_API_KEY=your-api-key-here

# Your model deployment name
MODEL_DEPLOYMENT_NAME=gpt-4o
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Project Structure

```
agentic-ui-v0/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   │   └── azure.py          # Azure configuration
│   │   ├── models/
│   │   │   └── models.py         # Pydantic models
│   │   ├── routers/
│   │   │   └── chat.py           # Chat API endpoints
│   │   └── services/
│   │       ├── agent.py          # Single AutoGen agent
│   │       └── session.py        # Session management
│   ├── main.py                   # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   └── .env.example             # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatInterface.vue # Chat UI component
│   │   ├── stores/
│   │   │   └── chat.ts          # Pinia chat store
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript types
│   │   ├── App.vue              # Main Vue app
│   │   └── main.ts              # Vue app entry
│   ├── package.json             # Node dependencies
│   └── vite.config.ts           # Vite configuration
├── start-dev.sh                 # Development startup script
├── test_smoke.py                # Functional smoke test
└── README.md                    # This file
```

## API Endpoints

- `POST /api/chat` - Send message and receive AutoGen AI response
- `GET /api/sessions/{session_id}/messages` - Retrieve conversation history
- `GET /health` - Health check with Azure configuration status

## Development

### Manual Startup

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Vue.js):**
```bash
cd frontend
npm install
npm run dev
```
